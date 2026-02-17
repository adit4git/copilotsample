# Kafka-Oracle Offset Commit Validation Guide
## Ensuring Exactly-Once Semantics: Offsets Only Commit After Successful DB Commit

**Purpose:** This document provides practical validation techniques to verify that Kafka offsets are committed ONLY after successful Oracle database commits, preventing data loss and duplicate processing.

---

## Table of Contents

1. [Core Validation Concept](#core-concept)
2. [Code-Level Validation](#code-validation)
3. [Database-Level Validation](#db-validation)
4. [Monitoring & Observability](#monitoring)
5. [Integration Testing](#testing)
6. [Production Audit Trail](#audit-trail)

---

## Core Validation Concept {#core-concept}

### The Requirement

```
Kafka Consumer receives message
              ↓
Process message in Oracle transaction
              ↓
DB COMMIT successful? 
    ├─ YES: Commit Kafka offset (safe to skip this message)
    └─ NO: ROLLBACK + Retry (will reprocess message)
```

**Critical:** Kafka offset commits MUST be inside the transaction boundary or explicitly ordered after DB commit.

### What Can Go Wrong

| Scenario | Problem | Impact |
|----------|---------|--------|
| Offset committed before DB commit | Consumer crashes mid-DB transaction | Data loss + duplicate processing |
| Offset committed on DB rollback | Message appears processed | Duplicate records (eventually) |
| Offset committed without checking commit result | DB fails silently | Data inconsistency |

---

## Code-Level Validation {#code-validation}

### Validation 1: Check Spring Batch Consumer Code Structure

**Correct Pattern (Spring Framework):**

```java
// ✅ CORRECT: Transactional method with offset commit inside transaction
@Transactional(rollbackFor = Exception.class)
@KafkaListener(topics = "cdc-topic", groupId = "my-consumer-group")
public void processCDCMessage(ConsumerRecord<String, String> record) {
    // Step 1: Parse and validate message
    CDCEvent event = parseCDCEvent(record.value());
    
    // Step 2: Check idempotency (inside transaction)
    if (isEventAlreadyProcessed(event.getEventId())) {
        log.info("Event {} already processed, skipping", event.getEventId());
        return; // Safe to exit - offset will still be committed
    }
    
    try {
        // Step 3: Update databases (inside transaction)
        updateAccountDimension(event);
        updateAccountFact(event);
        calculateOverlayDeltas(event);
        recordEventAsProcessed(event);
        
        // Step 4: Log offset (inside transaction)
        logCDCApplyState(record.partition(), record.offset());
        
        // Spring automatically commits offset AFTER @Transactional commits
        log.info("Successfully processed event {} at offset {}", 
                 event.getEventId(), record.offset());
    } catch (DataIntegrityException e) {
        // This triggers @Transactional rollback
        // Kafka offset is NOT committed
        log.error("Data integrity error, message will be reprocessed", e);
        throw e; // Spring handles the rollback
    }
}
```

**How to Validate:**

1. **Check for @Transactional annotation:**
   ```bash
   grep -r "@Transactional" src/main/java/com/company/cdc/
   # Should see: @Transactional on KafkaListener methods
   ```

2. **Verify offset commit happens after DB commit:**
   ```java
   // ✅✅ BEST PRACTICE: Explicit offset commit configuration
   @Configuration
   public class KafkaConfig {
       @Bean
       public ConcurrentKafkaListenerContainerFactory<String, String> 
               kafkaListenerContainerFactory(ConsumerFactory<String, String> consumerFactory) {
           ConcurrentKafkaListenerContainerFactory<String, String> factory = 
               new ConcurrentKafkaListenerContainerFactory<>();
           factory.setConsumerFactory(consumerFactory);
           
           // ✅ CRITICAL: Set to MANUAL - offset commit happens in transaction
           factory.getContainerProperties().setAckMode(MANUAL_IMMEDIATE);
           
           return factory;
       }
   }
   ```

3. **Check for exception handling:**
   ```java
   // VERIFY THIS EXISTS in your consumer code
   catch (Exception e) {
       log.error("Processing failed - DB transaction WILL rollback, " +
                 "Kafka offset will NOT be committed, message will be retried", e);
       throw e; // Force transaction rollback
   }
   ```

### Validation 2: Code Review Checklist

**Review your `SpringBatchConsumer.java` for:**

- [ ] **@Transactional present** on KafkaListener method?
- [ ] **@Transactional(rollbackFor = Exception.class)** to catch all exceptions?
- [ ] **AckMode = MANUAL_IMMEDIATE** or MANUAL configured?
- [ ] **Try-catch blocks** that re-throw exceptions (forcing rollback)?
- [ ] **No manual offset commit calls** before DB operations complete?
- [ ] **All DB operations in single transaction boundary**?

**Command to find violations:**

```bash
# Find all KafkaListener methods WITHOUT @Transactional
grep -B5 "@KafkaListener" src/main/java/com/company/cdc/*.java | grep -v "@Transactional"

# Should return: NOTHING (all should have @Transactional)
```

---

## Database-Level Validation {#db-validation}

### Validation 3: Check CDC_APPLY_STATE Tracking

**Purpose:** Verify that offsets are only recorded AFTER DB operations succeed.

**Schema (Design 2 from ADR-012):**

```sql
CREATE TABLE CDC_APPLY_STATE (
    consumer_group VARCHAR2(100),
    kafka_partition NUMBER,
    last_offset NUMBER,
    last_processed_event_id VARCHAR2(100),
    last_processed_timestamp TIMESTAMP,
    applied_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_cdc_apply PRIMARY KEY (consumer_group, kafka_partition)
);
```

**Validation Query 1: Check offset continuity (no gaps = good)**

```sql
-- ✅ This should show sequential offset increases (no gaps)
SELECT 
    kafka_partition,
    last_offset,
    LAG(last_offset) OVER (PARTITION BY kafka_partition ORDER BY applied_at) as prev_offset,
    LEAD(last_offset) OVER (PARTITION BY kafka_partition ORDER BY applied_at) as next_offset,
    applied_at,
    CASE 
        WHEN last_offset = LAG(last_offset) OVER (PARTITION BY kafka_partition ORDER BY applied_at) + 1
        THEN 'OK - Sequential'
        ELSE 'ANOMALY - Gap detected!'
    END as offset_check
FROM CDC_APPLY_STATE
WHERE consumer_group = 'my-consumer-group'
ORDER BY kafka_partition, applied_at DESC
FETCH FIRST 100 ROWS ONLY;
```

**What to look for:**
- ✅ **offset_check = "OK - Sequential"** for all rows → Offsets committed correctly
- ❌ **offset_check = "ANOMALY - Gap detected!"** → Offsets skipped (possible early commits)
- ❌ **Duplicate offsets** → Offsets committed multiple times (retry without rollback)

**Validation Query 2: Check timestamp ordering (offset time ≤ event time)**

```sql
-- ✅ Offset should not be recorded BEFORE event was processed
SELECT 
    c.last_offset,
    c.last_processed_event_id,
    c.applied_at as offset_committed_at,
    e.processed_at as event_processed_at,
    CASE 
        WHEN c.applied_at >= e.processed_at OR e.processed_at IS NULL
        THEN 'OK - Offset committed after event processing'
        ELSE 'ANOMALY - Offset committed BEFORE event processing!'
    END as timing_check
FROM CDC_APPLY_STATE c
LEFT JOIN ACCOUNT_EVENT_STATE e ON e.event_id = c.last_processed_event_id
WHERE c.consumer_group = 'my-consumer-group'
ORDER BY c.applied_at DESC
FETCH FIRST 50 ROWS ONLY;
```

**What to look for:**
- ✅ **timing_check = "OK - Offset committed after event processing"** for all rows
- ❌ **timing_check = "ANOMALY"** → Early offset commits (data loss risk!)

### Validation 4: Event State Idempotency Check

**Purpose:** Verify that duplicate messages (replayed from same offset) are properly handled.

```sql
-- ✅ This should show each event_id only once per account
SELECT 
    account_id,
    event_id,
    COUNT(*) as process_count,
    MAX(updated_ts) as last_processed
FROM ACCOUNT_EVENT_STATE
GROUP BY account_id, event_id
HAVING COUNT(*) > 1
ORDER BY process_count DESC;

-- Result set should be EMPTY if offset commit is working
-- If you see rows here: offset is being committed even on retry (bad!)
```

**Interpretation:**
- ✅ **Empty result set** → No duplicate event processing (offsets committed correctly)
- ❌ **Shows duplicates** → Same event processed 2+ times (offset committed on retry)

---

## Monitoring & Observability {#monitoring}

### Validation 5: Application Logging Verification

**Add these log statements to your consumer:**

```java
@Transactional(rollbackFor = Exception.class)
@KafkaListener(topics = "cdc-topic")
public void processCDCMessage(ConsumerRecord<String, String> record, Acknowledgment ack) {
    String eventId = "EVENT-" + record.offset() + "-" + record.partition();
    long txnStartTime = System.currentTimeMillis();
    
    try {
        log.info("[KAFKA-RCV] Received message: offset={}, partition={}, eventId={}", 
                 record.offset(), record.partition(), eventId);
        
        // Process message
        CDCEvent event = parseEvent(record.value());
        
        log.info("[DB-TXN-START] Starting DB transaction for eventId={}", eventId);
        updateAccountDimension(event);
        updateAccountFact(event);
        recordEventAsProcessed(event);
        log.info("[DB-TXN-END] Completed DB transaction for eventId={}", eventId);
        
        log.info("[OFFSET-COMMIT] Offset will be committed: offset={}, partition={}", 
                 record.offset(), record.partition());
        
    } catch (Exception e) {
        long errorTime = System.currentTimeMillis() - txnStartTime;
        log.error("[TXN-ROLLBACK] Transaction rolled back after {}ms for eventId={}: {}", 
                  errorTime, eventId, e.getMessage());
        throw e; // Trigger rollback
    }
}
```

**Log Pattern to Validate:**

```
[KAFKA-RCV] Received message: offset=1000, partition=0, eventId=EVENT-1000-0
[DB-TXN-START] Starting DB transaction for eventId=EVENT-1000-0
[DB-TXN-END] Completed DB transaction for eventId=EVENT-1000-0
[OFFSET-COMMIT] Offset will be committed: offset=1000, partition=0
```

✅ **Good log sequence:** Offset logged AFTER DB transaction ends

```
[KAFKA-RCV] Received message: offset=1001, partition=0, eventId=EVENT-1001-0
[DB-TXN-START] Starting DB transaction for eventId=EVENT-1001-0
[TXN-ROLLBACK] Transaction rolled back after 245ms for eventId=EVENT-1001-0: Duplicate key error
```

✅ **Good error handling:** Offset NOT logged after rollback

### Validation 6: Monitoring Metrics

**Add Micrometer metrics to track commit reliability:**

```java
@Component
public class KafkaOffsetMetrics {
    private final MeterRegistry meterRegistry;
    
    public KafkaOffsetMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }
    
    public void recordOffsetCommit(String partition, long offset, long processingTimeMs) {
        meterRegistry.timer("kafka.offset.commit.duration", 
            "partition", partition)
            .record(processingTimeMs, TimeUnit.MILLISECONDS);
        
        meterRegistry.counter("kafka.messages.processed", 
            "partition", partition)
            .increment();
    }
    
    public void recordOffsetRollback(String partition, String reason) {
        meterRegistry.counter("kafka.offset.rollback", 
            "partition", partition,
            "reason", reason)
            .increment();
    }
}
```

**Prometheus Queries to Run:**

```promql
# ✅ Check for offset regression (offsets moving backwards = data loss)
rate(kafka_consumer_lag_sum[5m]) < 0

# ✅ Check for high retry rate
rate(kafka.offset.rollback[5m]) > 0.1

# ✅ Check consumer is making progress
rate(kafka.messages.processed[5m]) > 0
```

---

## Integration Testing {#testing}

### Validation 7: Unit Test - Offset Only Commits on Success

```java
@SpringBootTest
@DirtiesContext
public class KafkaOffsetCommitTest {
    
    @Autowired
    private CDCConsumer cdcConsumer;
    
    @Autowired
    private AccountDimensionRepository accountDimRepo;
    
    @Autowired
    private CDCApplyStateRepository offsetRepo;
    
    @Test
    public void testOffsetOnlyCommitAfterSuccessfulDBCommit() {
        // GIVEN: A valid CDC message
        ConsumerRecord<String, String> message = createValidCDCMessage(
            offset = 1000,
            partition = 0,
            eventId = "EVT-001",
            accountId = 101,
            investmentType = "STOCK"
        );
        
        // WHEN: Message is processed successfully
        cdcConsumer.processCDCMessage(message);
        
        // THEN: Offset should be recorded in CDC_APPLY_STATE
        CDCApplyState offsetState = offsetRepo.findByPartitionAndConsumerGroup(0, "my-group");
        assertThat(offsetState.getLastOffset()).isEqualTo(1000);
        assertThat(offsetState.getLastProcessedEventId()).isEqualTo("EVT-001");
        
        // AND: Account dimension should be updated
        Account account = accountDimRepo.findById(101);
        assertThat(account.getInvestmentType()).isEqualTo("STOCK");
    }
    
    @Test
    public void testOffsetNotCommittedOnDBFailure() {
        // GIVEN: A CDC message that will cause data integrity error
        ConsumerRecord<String, String> message = createInvalidCDCMessage(
            offset = 1001,
            partition = 0,
            eventId = "EVT-002",
            investmentType = "INVALID"  // Will cause constraint violation
        );
        
        // WHEN: Message processing fails
        assertThrows(DataIntegrityException.class, () -> {
            cdcConsumer.processCDCMessage(message);
        });
        
        // THEN: Offset should NOT be recorded
        CDCApplyState offsetState = offsetRepo.findByPartitionAndConsumerGroup(0, "my-group");
        assertThat(offsetState.getLastOffset()).isNotEqualTo(1001);  // Still at previous offset
        
        // AND: NO changes should be made to ACCOUNT_DIM
        // (Transaction was rolled back)
        int accountCount = accountDimRepo.countByInvestmentType("INVALID");
        assertThat(accountCount).isEqualTo(0);
    }
    
    @Test
    public void testDuplicateMessageHandling() {
        // GIVEN: Process a message successfully (offset committed)
        ConsumerRecord<String, String> message = createValidCDCMessage(
            offset = 1002,
            eventId = "EVT-003"
        );
        cdcConsumer.processCDCMessage(message);
        CDCApplyState firstRun = offsetRepo.findByPartitionAndConsumerGroup(0, "my-group");
        assertThat(firstRun.getLastOffset()).isEqualTo(1002);
        
        // WHEN: Same message is replayed (offset 1002 again)
        cdcConsumer.processCDCMessage(message);
        
        // THEN: Offset should still be 1002 (not re-committed)
        CDCApplyState secondRun = offsetRepo.findByPartitionAndConsumerGroup(0, "my-group");
        assertThat(secondRun.getLastOffset()).isEqualTo(1002);
        
        // AND: Event should only exist once (not duplicated)
        AccountEventState eventState = eventStateRepo.findByEventId("EVT-003");
        assertThat(eventState.getProcessCount()).isEqualTo(1);
    }
}
```

### Validation 8: Integration Test - Offset Continuity

```java
@SpringBootTest
public class OffsetContinuityTest {
    
    @Autowired
    private CDCConsumer cdcConsumer;
    
    @Autowired
    private CDCApplyStateRepository offsetRepo;
    
    @Test
    public void testOffsetsContinuousWithoutGaps() {
        // GIVEN: Process 100 sequential messages
        for (int i = 0; i < 100; i++) {
            ConsumerRecord<String, String> msg = createValidCDCMessage(
                offset = 5000 + i,
                eventId = "EVT-" + i
            );
            cdcConsumer.processCDCMessage(msg);
        }
        
        // WHEN: Check offset progression
        List<CDCApplyState> offsets = offsetRepo.findAllByConsumerGroupOrderByAppliedAt("my-group");
        
        // THEN: Offsets should be sequential (no gaps, no duplicates)
        for (int i = 1; i < offsets.size(); i++) {
            long prevOffset = offsets.get(i - 1).getLastOffset();
            long currOffset = offsets.get(i).getLastOffset();
            
            // Each offset should be exactly 1 more than previous
            assertThat(currOffset).isEqualTo(prevOffset + 1);
        }
    }
}
```

---

## Production Audit Trail {#audit-trail}

### Validation 9: Automated Daily Health Check

**SQL Script to run daily:**

```sql
-- Daily offset commit validation
DECLARE
    v_consumer_group VARCHAR2(100) := 'my-consumer-group';
    v_critical_alerts NUMBER := 0;
    v_warning_alerts NUMBER := 0;
BEGIN
    -- Check 1: Lastly processed offset matches event count
    SELECT COUNT(*) INTO v_critical_alerts 
    FROM (
        SELECT partition, COUNT(*) as event_count, MAX(offset) as max_offset
        FROM CDC_APPLY_STATE
        WHERE consumer_group = v_consumer_group
        GROUP BY partition
        HAVING COUNT(*) != MAX(offset) - MIN(offset) + 1
    );
    
    IF v_critical_alerts > 0 THEN
        DBMS_OUTPUT.PUT_LINE('🚨 CRITICAL: Offset gaps detected! Events may be skipped.');
    END IF;
    
    -- Check 2: Duplicate event processing
    SELECT COUNT(*) INTO v_warning_alerts
    FROM (
        SELECT event_id, COUNT(*)
        FROM ACCOUNT_EVENT_STATE
        WHERE processed_at > TRUNC(SYSDATE)
        GROUP BY event_id
        HAVING COUNT(*) > 1
    );
    
    IF v_warning_alerts > 0 THEN
        DBMS_OUTPUT.PUT_LINE('⚠️  WARNING: ' || v_warning_alerts || ' events processed multiple times.');
    END IF;
    
    -- Check 3: Recent offset commits
    SELECT COUNT(*) INTO v_critical_alerts
    FROM CDC_APPLY_STATE
    WHERE consumer_group = v_consumer_group
    AND applied_at < SYSDATE - 5/1440;  -- No commits in last 5 minutes
    
    IF v_critical_alerts = 0 THEN
        DBMS_OUTPUT.PUT_LINE('✅ HEALTHY: Offsets being committed normally.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('⚠️  WARNING: No offset commits in last 5 minutes - consumer may be stalled.');
    END IF;
END;
/
```

### Validation 10: Offset Audit Report

**Monthly validation report to generate:**

```sql
CREATE OR REPLACE VIEW OFFSET_AUDIT_REPORT AS
SELECT 
    consumer_group,
    kafka_partition,
    MIN(applied_at) as first_offset_commit,
    MAX(applied_at) as latest_offset_commit,
    COUNT(*) as total_offsets_committed,
    MAX(last_offset) - MIN(last_offset) as offset_range,
    CASE 
        WHEN (COUNT(*) = MAX(last_offset) - MIN(last_offset) + 1)
        THEN '✅ Sequential (Good)'
        ELSE '❌ Gaps Detected'
    END as offset_continuity,
    ROUND(AVG(UNIX_TIMESTAMP(applied_at) - UNIX_TIMESTAMP(LAG(applied_at) OVER (ORDER BY applied_at))), 2) as avg_commit_interval_sec
FROM CDC_APPLY_STATE
GROUP BY consumer_group, kafka_partition;

-- Run monthly:
SELECT * FROM OFFSET_AUDIT_REPORT
ORDER BY consumer_group, kafka_partition;
```

---

## Quick Validation Checklist

**Run these to validate offset commit safety:**

- [ ] ✅ All @KafkaListener methods have @Transactional annotation
- [ ] ✅ AckMode is set to MANUAL or MANUAL_IMMEDIATE
- [ ] ✅ CDC_APPLY_STATE shows sequential offsets (no gaps)
- [ ] ✅ ACCOUNT_EVENT_STATE shows no duplicates for same event_id
- [ ] ✅ Application logs show "OFFSET-COMMIT" AFTER "DB-TXN-END"
- [ ] ✅ Integration tests pass (commit on success, no commit on failure)
- [ ] ✅ Daily health check reports "HEALTHY"
- [ ] ✅ Kafka consumer lag is stable (not growing)
- [ ] ✅ No"ANOMALY" messages in offset continuity query

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-16  
**Author:** Technical Validation Team
