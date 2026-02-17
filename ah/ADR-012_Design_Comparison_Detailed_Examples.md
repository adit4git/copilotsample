# ADR-012: Detailed Design Comparison with Examples
## Oracle Schema Design for Rolling ±90-Day Account Summary + Detail Grids

**Document Purpose:** This document provides a thorough, non-technical explanation of two database design approaches, showing exactly how data flows through the system from nightly feeds, through intraday updates, to UI screens.

---

## Table of Contents

1. [Overview: What Are We Building?](#overview)
2. [Design Approach 1: Main Design (v5) - Type 1 SCD with Snapshots](#design-1-main)
3. [Design Approach 2: Gilfoyle Revised - Type 2 SCD Simplified](#design-2-gilfoyle)
4. [Side-by-Side Comparison with Real Data](#comparison)
5. [Service Plan and Service Run (DCA/TET) in Both Designs](#service-plan-run)
6. [Kafka Reliability: Can We Rely on It When Interacting with the DB?](#kafka-reliability)
7. [Conclusion and Recommendation](#conclusion)

---

## Overview: What Are We Building? {#overview}

### The Business Problem

Imagine you're managing a financial dashboard that shows:
- **Summary Grid:** "How many accounts need rebalancing in the next 30 days?" or "How many accounts have QLH scheduled for next week?"
- **Detail Grid:** "Show me all accounts for client 'Smith' with assets over $100,000"

The system needs to:
- Handle **10 million accounts**
- Update data **nightly** (bulk load) and **throughout the day** (real-time updates)
- Show **accurate historical data** (what was the account status 6 months ago?)
- Respond **quickly** (< 300ms for queries)

### Two Different Approaches

**Design 1 (Main v5):** Uses "snapshot columns" - copies dimension values into fact tables to preserve history
**Design 2 (Gilfoyle Revised):** Uses "Type 2 Slowly Changing Dimensions" - creates new dimension rows when values change

Both work, but they handle data differently. Let's see how...

---

## Design Approach 1: Main Design (v5) - Type 1 SCD with Snapshots {#design-1-main}

### Core Concept
**"Take a picture of dimension values and store them in the fact table"**

When an account's investment type changes from "ETF" to "STOCK", the dimension table gets updated (overwritten), but we also copy the old value into the fact table's snapshot columns so we remember what it was.

### Table Structure

#### 1. ACCOUNT_DIM (Dimension Table - Current Values Only)

This table stores the **current** state of account attributes. When values change, they're **overwritten**.

| account_id | account_number | client_name | investment_type | status | region_code | qlh_enrolled_yn | qlh_enroll_dt | dim_version | last_updated_ts |
|------------|----------------|-------------|-----------------|--------|-------------|-----------------|--------------|-------------|------------------|
| 101 | A-0000123456 | John Smith | ETF | ACTIVE | NE | Y | 2025-12-01 | 3 | 2026-02-11 08:00:00 |
| 102 | A-0000654321 | Jane Patel | MF | ACTIVE | SE | Y | 2026-01-15 | 1 | 2026-02-11 08:00:00 |
| 103 | A-0000789012 | Bob Johnson | STOCK | ACTIVE | CA | N | NULL | 2 | 2026-02-11 08:00:00 |

**Key Points:**
- `dim_version` increments each time any attribute changes (currently John Smith's account has been updated 3 times)
- Only **current** values are stored here
- Historical values are preserved in the fact table's snapshot columns

#### 2. ACCOUNT_DAY_FCT (Fact Table - Daily Snapshots with Dimension Copies)

This table stores **daily snapshots** of account state, including **copies** of dimension values at that point in time.

| snap_dt | account_id | asset_value | rebalance_dt | qlh_next_run_dt | dim_investment_type_snap | dim_status_snap | dim_region_code_snap | dim_version_snap |
|---------|------------|-------------|--------------|-----------------|-------------------------|-----------------|---------------------|------------------|
| 2026-02-10 | 101 | 250000 | 2026-03-05 | 2026-03-02 | ETF | ACTIVE | NE | 2 |
| 2026-02-11 | 101 | 255000 | 2026-03-05 | 2026-03-02 | ETF | ACTIVE | NE | 3 |
| 2026-02-10 | 102 | 120000 | 2026-02-01 | 2026-04-16 | MF | ACTIVE | SE | 1 |
| 2026-02-11 | 102 | 122000 | 2026-02-15 | 2026-04-16 | MF | ACTIVE | SE | 1 |

**Key Points:**
- Each row represents one account on one day
- `dim_*_snap` columns are **copies** of dimension values at that time
- These snapshot columns preserve history even if dimension table changes

#### 3. SUMMARY_HOT_OVERLAY (Real-Time Adjustments)

This table tracks **changes** that happen between materialized view refreshes.

| snap_dt | summary_type | dimension_key | bucket_value | delta_count | last_updated_ts |
|---------|--------------|---------------|--------------|-------------|-----------------|
| 2026-02-11 | REBALANCE | ETF\|NE\|ACTIVE | 0_30_DAYS | +1 | 2026-02-11 14:30:00 |
| 2026-02-11 | REBALANCE | ETF\|NE\|ACTIVE | 31_60_DAYS | -1 | 2026-02-11 14:30:00 |
| 2026-02-11 | QLH_WEEKLY | MF\|SE\|ACTIVE | 2026-04-14 | +1 | 2026-02-11 15:15:00 |

**Key Points:**
- Stores **deltas** (+1, -1) not absolute counts
- Used to bridge the gap between MV refreshes (which happen every 15-30 minutes)
- Gets truncated after each MV refresh

#### 4. ACCOUNT_EVENT_STATE (Idempotency Tracking)

Prevents processing the same Kafka message twice.

| account_id | last_event_id | last_event_ts | updated_ts |
|------------|---------------|---------------|------------|
| 101 | IIDR-20260211-143000-001 | 2026-02-11 14:30:00 | 2026-02-11 14:30:05 |
| 102 | IIDR-20260211-151500-002 | 2026-02-11 15:15:00 | 2026-02-11 15:15:03 |

**Key Points:**
- Tracks which events have been processed
- Prevents duplicate processing if Kafka retries

#### 5. CDC_APPLY_STATE (Kafka Offset Tracking)

Tracks Kafka consumer progress.

| topic | partition_id | last_offset | last_event_ts | updated_ts |
|-------|--------------|-------------|---------------|------------|
| account-updates | 0 | 15234 | 2026-02-11 15:30:00 | 2026-02-11 15:30:05 |
| account-updates | 1 | 14892 | 2026-02-11 15:30:00 | 2026-02-11 15:30:05 |

---

### Scenario Walkthrough: Design 1

#### Initial State (After Nightly Feed on 2026-02-11)

**Step 1: Nightly Bulk Feed Processing**

The system receives a bulk file with all account data:

```
Account Number: A-0000123456
Client Name: John Smith
Investment Type: ETF
Status: ACTIVE
Region: NE
Asset Value: 250000
Rebalance Date: 2026-03-05
QLH Enrolled: Yes
QLH Enrollment Date: 2025-12-01
```

**Processing Steps:**

1. **Load to Staging Table:**
   ```
   ACCOUNT_STG:
   account_number: A-0000123456
   client_name: John Smith
   investment_type: ETF
   status: ACTIVE
   region_code: NE
   asset_value: 250000
   rebalance_dt: 2026-03-05
   qlh_enroll_dt: 2025-12-01
   ```

2. **Update Dimension (Type 1 - Overwrite):**
   ```sql
   MERGE INTO ACCOUNT_DIM
   -- If account exists, UPDATE all columns
   -- If new, INSERT new row
   ```
   
   **Result:**
   | account_id | account_number | investment_type | status | dim_version |
   |------------|----------------|-----------------|--------|-------------|
   | 101 | A-0000123456 | ETF | ACTIVE | 3 |

3. **Calculate Derived Fields:**
   - QLH next run date = 2025-12-01 + (91 days × cycles) = 2026-03-02

4. **Update PLAN and RUN (DCA/TET):**
   - MERGE ACCOUNT_SERVICE_PLAN from staging (enrollment, status, next_due_dt, etc.).
   - Bulk insert new rows into ACCOUNT_SERVICE_RUN (completed executions).
   - Today’s fact snapshot columns (dca_plan_status, tet_plan_status, dca_next_due_dt, tet_next_due_dt) are populated from PLAN when building the fact. *(Full flow in [Service Plan and Service Run](#service-plan-run).)*

5. **Insert/Update Fact Table:**
   ```sql
   MERGE INTO ACCOUNT_DAY_FCT
   -- Copy dimension values into snapshot columns; include dca_*, tet_* from PLAN
   ```
   
   **Result:**
   | snap_dt | account_id | asset_value | dim_investment_type_snap | dim_status_snap | dim_version_snap |
   |---------|------------|-------------|-------------------------|-----------------|-----------------|
   | 2026-02-11 | 101 | 250000 | ETF | ACTIVE | 3 |

6. **Refresh Materialized Views:**
   ```sql
   REFRESH COMPLETE mv_rebalance_summary;
   REFRESH COMPLETE mv_qlh_weekly;
   ```
   *(These MVs are built from ACCOUNT_DAY_FCT only; DCA/TET KPIs use PLAN/RUN directly. See [Service Plan and Service Run](#service-plan-run).)*

7. **Truncate Overlay:**
   ```sql
   TRUNCATE TABLE SUMMARY_HOT_OVERLAY;
   ```

*(Intraday CDC also updates ACCOUNT_SERVICE_PLAN and ACCOUNT_SERVICE_RUN, and today’s fact snapshot columns; see [Service Plan and Service Run](#service-plan-run).)*

---

#### Intraday Update Scenario (Design 1)

**Time: 2026-02-11 14:30:00**

**Event:** John Smith's account (A-0000123456) changes investment type from "ETF" to "STOCK"

**Kafka Message Received:**
```json
{
  "event_id": "IIDR-20260211-143000-001",
  "account_number": "A-0000123456",
  "investment_type": "STOCK",
  "event_timestamp": "2026-02-11T14:30:00Z"
}
```

**Processing Steps:**

1. **Check Idempotency:**
   ```sql
   SELECT last_event_id FROM ACCOUNT_EVENT_STATE 
   WHERE account_id = 101;
   -- Returns: NULL (first time processing this account today)
   ```

2. **Update Dimension (Type 1):**
   ```sql
   UPDATE ACCOUNT_DIM
   SET investment_type = 'STOCK',
       dim_version = dim_version + 1,  -- Increment: 3 → 4
       last_updated_ts = SYSTIMESTAMP
   WHERE account_id = 101;
   ```
   
   **Result:**
   | account_id | investment_type | dim_version |
   |------------|-----------------|-------------|
   | 101 | STOCK | 4 |

3. **Update Fact Table (Today's Row):**
   ```sql
   MERGE INTO ACCOUNT_DAY_FCT
   -- Update today's row with new snapshot values
   ```
   
   **Result:**
   | snap_dt | account_id | dim_investment_type_snap | dim_version_snap |
   |---------|------------|-------------------------|------------------|
   | 2026-02-11 | 101 | STOCK | 4 |

4. **Calculate Overlay Deltas:**
   - **Before:** Account was in bucket "ETF|NE|ACTIVE" → "31_60_DAYS"
   - **After:** Account is now in bucket "STOCK|NE|ACTIVE" → "31_60_DAYS"
   - **Delta:** -1 from old bucket, +1 to new bucket

5. **Update Overlay Table:**
   ```sql
   INSERT INTO SUMMARY_HOT_OVERLAY VALUES
   ('2026-02-11', 'REBALANCE', 'ETF|NE|ACTIVE', '31_60_DAYS', -1, ...);
   INSERT INTO SUMMARY_HOT_OVERLAY VALUES
   ('2026-02-11', 'REBALANCE', 'STOCK|NE|ACTIVE', '31_60_DAYS', +1, ...);
   ```

6. **Update Event State:**
   ```sql
   INSERT INTO ACCOUNT_EVENT_STATE VALUES
   (101, 'IIDR-20260211-143000-001', '2026-02-11 14:30:00', ...);
   ```

7. **Commit Transaction**

**Total Operations:** 7 database operations per message

---

#### UI Query: Summary Grid (Design 1)

**User Request:** "Show me rebalance summary for today"

**Query Execution:**

1. **Query Materialized View:**
   ```sql
   SELECT rebalance_bucket, investment_type, COUNT(*) as account_count
   FROM mv_rebalance_summary
   WHERE snap_dt = '2026-02-11'
   GROUP BY rebalance_bucket, investment_type;
   ```
   
   **Result:**
   | rebalance_bucket | investment_type | account_count |
   |------------------|-----------------|---------------|
   | 0_30_DAYS | ETF | 1500 |
   | 31_60_DAYS | ETF | 2300 |
   | 31_60_DAYS | STOCK | 1800 |

2. **Add Overlay Deltas:**
   ```sql
   SELECT dimension_key, bucket_value, SUM(delta_count) as delta
   FROM SUMMARY_HOT_OVERLAY
   WHERE snap_dt = '2026-02-11'
   GROUP BY dimension_key, bucket_value;
   ```
   
   **Result:**
   | dimension_key | bucket_value | delta |
   |---------------|--------------|-------|
   | ETF|NE|ACTIVE | 31_60_DAYS | -1 |
   | STOCK|NE|ACTIVE | 31_60_DAYS | +1 |

3. **Combine Results:**
   - ETF 31_60_DAYS: 2300 - 1 = 2299
   - STOCK 31_60_DAYS: 1800 + 1 = 1801

**Final Display:**
| Rebalance Bucket | Investment Type | Account Count |
|------------------|-----------------|---------------|
| 0-30 Days | ETF | 1,500 |
| 31-60 Days | ETF | 2,299 |
| 31-60 Days | STOCK | 1,801 |

---

#### UI Query: Detail Grid (Design 1)

**User Request:** "Show me all accounts with investment type 'STOCK' and assets > $200,000"

**Query:**
```sql
SELECT 
  d.account_number,
  d.client_name,
  f.asset_value,
  f.dim_investment_type_snap,  -- Using snapshot column!
  f.rebalance_dt
FROM ACCOUNT_DAY_FCT f
JOIN ACCOUNT_DIM d ON d.account_id = f.account_id
WHERE f.snap_dt = '2026-02-11'
  AND f.dim_investment_type_snap = 'STOCK'  -- Filter on snapshot
  AND f.asset_value > 200000
ORDER BY d.account_number
FETCH FIRST 50 ROWS ONLY;
```

**Result:**
| account_number | client_name | asset_value | investment_type | rebalance_dt |
|----------------|-------------|-------------|-----------------|--------------|
| A-0000123456 | John Smith | 255000 | STOCK | 2026-03-05 |
| A-0000456789 | Alice Brown | 320000 | STOCK | 2026-04-10 |

**Key Point:** We filter on `dim_investment_type_snap` (the snapshot column) to get accurate "as-of-today" values, even if the dimension table was updated later.

---

## Design Approach 2: Gilfoyle Revised - Type 2 SCD Simplified {#design-2-gilfoyle}

### Core Concept
**"Create a new dimension row when values change, and link fact rows to the correct dimension version"**

When an account's investment type changes from "ETF" to "STOCK", we:
1. Close the old dimension row (set `effective_to_dt`)
2. Create a new dimension row (set `effective_from_dt`)
3. Update fact rows to point to the new dimension key

### Table Structure

#### 1. ACCOUNT_DIM (Type 2 SCD - Historical Versions)

This table stores **all versions** of account attributes with effective dating.

| account_dim_key | account_number | client_name | investment_type | status | region_code | effective_from_dt | effective_to_dt | is_current |
|-----------------|----------------|-------------|-----------------|--------|-------------|-------------------|-----------------|------------|
| 1001 | A-0000123456 | John Smith | ETF | ACTIVE | NE | 2025-01-01 | 2026-02-11 | N |
| 1002 | A-0000123456 | John Smith | STOCK | ACTIVE | NE | 2026-02-11 | 9999-12-31 | Y |
| 1003 | A-0000654321 | Jane Patel | MF | ACTIVE | SE | 2026-01-15 | 9999-12-31 | Y |
| 1004 | A-0000789012 | Bob Johnson | STOCK | ACTIVE | CA | 2025-06-01 | 9999-12-31 | Y |

**Key Points:**
- Each change creates a **new row** with a new `account_dim_key`
- `effective_from_dt` and `effective_to_dt` define when this version was valid
- `is_current = 'Y'` marks the current version
- Historical versions are preserved automatically

#### 2. ACCOUNT_FACT (Fact Table - Links to Dimension Versions)

This table stores daily snapshots with a **foreign key** to the dimension version that was valid at that time.

| snap_dt | account_number | account_dim_key | asset_value | rebalance_dt | qlh_next_run_dt |
|---------|----------------|-----------------|-------------|--------------|-----------------|
| 2026-02-10 | A-0000123456 | 1001 | 250000 | 2026-03-05 | 2026-03-02 |
| 2026-02-11 | A-0000123456 | 1002 | 255000 | 2026-03-05 | 2026-03-02 |
| 2026-02-10 | A-0000654321 | 1003 | 120000 | 2026-02-01 | 2026-04-16 |
| 2026-02-11 | A-0000654321 | 1003 | 122000 | 2026-02-15 | 2026-04-16 |

**Key Points:**
- `account_dim_key` points to the dimension row that was valid at `snap_dt`
- No snapshot columns needed - we join to dimension to get attributes
- Historical queries join to dimension and filter by effective dates

#### 3. SERVICE_PLAN (DCA/TET Enrollment)

| service_plan_id | account_number | service_type | enrolled_dt | status | expected_completion |
|-----------------|----------------|--------------|-------------|--------|---------------------|
| 2001 | A-0000123456 | DCA | 2026-01-01 | ACTIVE | 2028-01-01 |
| 2002 | A-0000654321 | TET | 2025-12-01 | ACTIVE | NULL |

#### 4. SERVICE_RUN (Execution Events)

| service_run_id | service_plan_id | account_number | service_type | run_dt | run_status | amount_processed |
|----------------|-----------------|----------------|--------------|--------|------------|------------------|
| 3001 | 2001 | A-0000123456 | DCA | 2026-02-01 | COMPLETED | 5000 |
| 3002 | 2001 | A-0000123456 | DCA | 2026-03-01 | COMPLETED | 5000 |

**Note:** No overlay table, no event state table - these are eliminated!

#### 5. Staging Tables (Temporary - Not Part of Permanent Schema)

**ACCOUNT_STG** - Temporary staging table used only during nightly batch processing:
- Loaded from bulk feed files
- Used for validation and transformation
- Source for partition exchange operation
- Truncated/dropped after processing completes

**account_fact_exch** - Temporary exchange table:
- Built from ACCOUNT_STG during nightly batch
- Used for partition exchange operation
- Dropped immediately after exchange completes

**Key Point:** Staging tables are temporary operational tables, not permanent schema objects. They exist only during batch processing windows and are cleaned up afterward.

---

### Scenario Walkthrough: Design 2

#### Initial State (After Nightly Feed on 2026-02-11)

**Step 1: Nightly Bulk Feed Processing**

Same bulk file as Design 1:

```
Account Number: A-0000123456
Client Name: John Smith
Investment Type: ETF
Status: ACTIVE
Region: NE
Asset Value: 250000
Rebalance Date: 2026-03-05
QLH Enrolled: Yes
QLH Enrollment Date: 2025-12-01
```

**Processing Steps:**

1. **Load to Staging Table:**
   ```
   ACCOUNT_STG:
   account_number: A-0000123456
   client_name: John Smith
   investment_type: ETF
   status: ACTIVE
   region_code: NE
   asset_value: 250000
   rebalance_dt: 2026-03-05
   qlh_enroll_dt: 2025-12-01
   ```
   
   **Note:** Staging tables are temporary tables used only during batch processing. They are truncated/dropped after processing completes.

2. **Validate and Transform:**
   - Apply business rules
   - Compute derived fields (QLH next_run_dt)
   - Join to current dimensions to get account_dim_key

3. **Check Dimension Changes:**
   ```sql
   SELECT account_dim_key, investment_type, status
   FROM ACCOUNT_DIM
   WHERE account_number = 'A-0000123456'
     AND is_current = 'Y';
   ```
   
   **Result:** No current row exists (new account)

3. **Insert New Dimension Row (Type 2):**
   ```sql
   INSERT INTO ACCOUNT_DIM (
     account_number, client_name, investment_type, status, region_code,
     effective_from_dt, effective_to_dt, is_current
   ) VALUES (
     'A-0000123456', 'John Smith', 'ETF', 'ACTIVE', 'NE',
     '2026-02-11', '9999-12-31', 'Y'
   );
   ```
   
   **Result:**
   | account_dim_key | account_number | investment_type | effective_from_dt | is_current |
   |-----------------|----------------|-----------------|-------------------|------------|
   | 1001 | A-0000123456 | ETF | 2026-02-11 | Y |

4. **Update SERVICE_PLAN and SERVICE_RUN (DCA/TET):**
   - MERGE SERVICE_PLAN from staging (enrollment, status, expected_completion, etc.).
   - Bulk insert new rows into SERVICE_RUN (completed executions).
   - ACCOUNT_FACT does not store DCA/TET columns; DCA/TET KPIs are queried directly from SERVICE_PLAN and SERVICE_RUN. *(Full flow in [Service Plan and Service Run](#service-plan-run).)*

5. **Build Exchange Partition Table:**
   ```sql
   -- Create exchange table with today's data from staging
   CREATE TABLE account_fact_exch AS
   SELECT 
     TRUNC(SYSDATE) AS snap_dt,
     s.account_number,
     d.account_dim_key,
     s.asset_value,
     s.rebalance_dt,
     s.qlh_enrollment_dt,
     s.qlh_last_run_dt,
     calc_qlh_next_run(s.qlh_enrollment_dt, TRUNC(SYSDATE)) AS qlh_next_run_dt,
     SYSTIMESTAMP AS created_ts,
     SYSTIMESTAMP AS updated_ts
   FROM account_stg s
   JOIN account_dim d ON d.account_number = s.account_number
                      AND d.is_current = 'Y';
   
   -- Add constraints to exchange table
   ALTER TABLE account_fact_exch
     ADD CONSTRAINT exch_pk PRIMARY KEY (snap_dt, account_number);
   ```
   
   **Key Point:** This creates a complete partition's worth of data in a separate table before swapping it in.

6. **Exchange Partition (Instant Operation):**
   ```sql
   -- Swap exchange table with partition (instant operation)
   ALTER TABLE account_fact
     EXCHANGE PARTITION FOR (TRUNC(SYSDATE))
     WITH TABLE account_fact_exch
     INCLUDING INDEXES
     WITHOUT VALIDATION;
   ```
   
   **Result:**
   | snap_dt | account_number | account_dim_key | asset_value |
   |---------|----------------|-----------------|-------------|
   | 2026-02-11 | A-0000123456 | 1001 | 250000 |
   
   **Key Point:** Partition exchange is an instant metadata operation - no data movement required. This is much faster than INSERT/UPDATE operations.

7. **Refresh Materialized Views (FAST):**
   ```sql
   REFRESH FAST mv_rebalance_summary;
   REFRESH FAST mv_qlh_weekly;
   ```
   
   **Note:** FAST refresh takes <5 seconds vs COMPLETE which takes 1-2 minutes. *(mv_rebalance_summary and mv_qlh_weekly are from ACCOUNT_FACT only; DCA/TET KPIs use SERVICE_PLAN/SERVICE_RUN directly. See [Service Plan and Service Run](#service-plan-run).)*

8. **Cleanup:**
   ```sql
   TRUNCATE TABLE account_stg;  -- Clear staging table
   DROP TABLE account_fact_exch; -- Drop exchange table
   ```
   
   **Key Point:** Staging tables are temporary and cleaned up after processing. They are not part of the permanent schema.

---

#### Intraday Update Scenario (Design 2)

**Time: 2026-02-11 14:30:00**

**Event:** John Smith's account changes investment type from "ETF" to "STOCK"

**Kafka Message Received:**
```json
{
  "event_id": "IIDR-20260211-143000-001",
  "account_number": "A-0000123456",
  "investment_type": "STOCK",
  "event_timestamp": "2026-02-11T14:30:00Z"
}
```

**Processing Steps (All in One Transaction):**

1. **Close Current Dimension Row:**
   ```sql
   UPDATE ACCOUNT_DIM
   SET effective_to_dt = '2026-02-11',
       is_current = 'N'
   WHERE account_number = 'A-0000123456'
     AND is_current = 'Y';
   ```
   
   **Result:**
   | account_dim_key | investment_type | effective_to_dt | is_current |
   |-----------------|-----------------|-----------------|------------|
   | 1001 | ETF | 2026-02-11 | N |

2. **Insert New Dimension Row:**
   ```sql
   INSERT INTO ACCOUNT_DIM (
     account_number, investment_type, status, region_code,
     effective_from_dt, effective_to_dt, is_current
   ) VALUES (
     'A-0000123456', 'STOCK', 'ACTIVE', 'NE',
     '2026-02-11', '9999-12-31', 'Y'
   );
   ```
   
   **Result:**
   | account_dim_key | investment_type | effective_from_dt | is_current |
   |-----------------|-----------------|-------------------|------------|
   | 1002 | STOCK | 2026-02-11 | Y |

3. **Update Fact Table FK:**
   ```sql
   UPDATE ACCOUNT_FACT
   SET account_dim_key = 1002
   WHERE account_number = 'A-0000123456'
     AND snap_dt >= '2026-02-11';
   ```
   
   **Result:**
   | snap_dt | account_number | account_dim_key |
   |---------|----------------|-----------------|
   | 2026-02-11 | A-0000123456 | 1002 |

4. **Kafka Offset Committed Automatically** (framework handles this)

**Total Operations:** 1 transaction with 3 SQL statements (vs 7 separate operations in Design 1)

**No Overlay Updates Needed!** Materialized views will be refreshed in 5 minutes automatically.

---

#### UI Query: Summary Grid (Design 2)

**User Request:** "Show me rebalance summary for today"

**Query:**
```sql
SELECT 
  rebalance_bucket,
  investment_type,
  SUM(account_count) as total_accounts
FROM mv_rebalance_summary
WHERE snap_dt = '2026-02-11'
GROUP BY rebalance_bucket, investment_type
ORDER BY rebalance_bucket;
```

**Result:**
| rebalance_bucket | investment_type | total_accounts |
|------------------|-----------------|-----------------|
| 0-30 Days | ETF | 1,500 |
| 31-60 Days | ETF | 2,299 |
| 31-60 Days | STOCK | 1,801 |

**Key Point:** No overlay table to query - MV contains current data (refreshed every 5 minutes)

---

#### UI Query: Detail Grid (Design 2)

**User Request:** "Show me all accounts with investment type 'STOCK' and assets > $200,000"

**Query:**
```sql
SELECT 
  d.account_number,
  d.client_name,
  f.asset_value,
  d.investment_type,  -- Join to dimension!
  f.rebalance_dt
FROM ACCOUNT_FACT f
JOIN ACCOUNT_DIM d ON d.account_dim_key = f.account_dim_key
WHERE f.snap_dt = '2026-02-11'
  AND d.is_current = 'Y'  -- Only current dimension version
  AND d.investment_type = 'STOCK'
  AND f.asset_value > 200000
ORDER BY d.account_number
FETCH FIRST 50 ROWS ONLY;
```

**Result:**
| account_number | client_name | asset_value | investment_type | rebalance_dt |
|----------------|-------------|-------------|-----------------|--------------|
| A-0000123456 | John Smith | 255000 | STOCK | 2026-03-05 |
| A-0000456789 | Alice Brown | 320000 | STOCK | 2026-04-10 |

**Key Point:** We join to dimension and filter on `is_current = 'Y'` to get current values.

---

#### Historical Query Example (Design 2)

**User Request:** "What was John Smith's investment type on 2026-02-10?"

**Query:**
```sql
SELECT 
  f.snap_dt,
  d.account_number,
  d.client_name,
  d.investment_type  -- Historical value!
FROM ACCOUNT_FACT f
JOIN ACCOUNT_DIM d ON d.account_dim_key = f.account_dim_key
WHERE f.account_number = 'A-0000123456'
  AND f.snap_dt = '2026-02-10'
  AND d.effective_from_dt <= f.snap_dt
  AND d.effective_to_dt > f.snap_dt;  -- Dimension valid at snap_dt
```

**Result:**
| snap_dt | account_number | client_name | investment_type |
|---------|----------------|-------------|-----------------|
| 2026-02-10 | A-0000123456 | John Smith | ETF |

**Explanation:**
- Fact row for 2026-02-10 has `account_dim_key = 1001`
- Dimension row 1001 has `investment_type = 'ETF'` and was valid from 2025-01-01 to 2026-02-11
- Since 2026-02-10 falls within that range, we get "ETF"

---

## Nightly Batch Strategies: Partition Exchange vs Full Merge {#batch-strategies}

### Design 1: Full Merge Strategy

**Overview:**
Design 1 uses the `MERGE` statement to combine staged data with the existing fact table. This approach must check every row in the target partition and decide whether to update or insert.

**Process Flow:**

```
Input: ACCOUNT_STG (10M rows from nightly feed)
↓
MERGE INTO ACCOUNT_DAY_FCT USING ACCOUNT_STG
├─ For each row in ACCOUNT_STG:
│  ├─ Query ACCOUNT_DAY_FCT (lookup by snap_dt, account_id)
│  ├─ Compare values
│  ├─ If found: UPDATE + log changes
│  └─ If not found: INSERT + log new
├─ Undo/Redo logging for each operation
├─ Row-by-row updates to partition
└─ Output: Updated ACCOUNT_DAY_FCT partition

Duration: 30-45 minutes (10M rows × row operations)
↓
MV REFRESH COMPLETE (Full Reconstruction)
├─ SELECT * FROM ACCOUNT_DAY_FCT
│  └─ Scan entire partition (10M+ rows)
├─ Join to ACCOUNT_DIM
├─ Aggregate by rebalance/qlh buckets
├─ Rebuild materialized view from scratch
└─ Output: Updated MV_REBALANCE_SUMMARY, MV_QLH_WEEKLY

Duration: 1-2 minutes (full table scan required)
```

**Characteristics:**
- ✗ Row-by-row operations on 10M rows
- ✗ Full logging overhead for recoverability
- ✗ Extended table locks (45+ minutes)
- ✗ MV Reconstruction requires full scan of base table

---

### Design 2: Partition Exchange Strategy

**Overview:**
Design 2 uses partition exchange to swap an pre-built partition into place. The data is built in a separate table (exchange table) with all transformations applied, then the entire partition is swapped in using metadata operations only.

**Process Flow:**

```
Input: ACCOUNT_STG (10M rows from nightly feed)
↓
Step 1: Build Exchange Partition
├─ CREATE TABLE account_fact_exch AS
│  ├─ SELECT s.*, d.account_dim_key
│  ├─ FROM account_stg s
│  ├─ JOIN account_dim d ON d.account_number = s.account_number
│  └─ For today's partition (10M rows)
├─ Build indexes on exchange table
└─ Duration: 2-3 minutes (organized insert, no logging)

↓
Step 2: Partition Exchange (Instant - Metadata Only)
├─ ALTER TABLE account_fact
│  └─ EXCHANGE PARTITION event_date = TRUNC(SYSDATE)
│     WITH TABLE account_fact_exch
│     ├─ Verify both partitions have identical structure
│     └─ Swap pointers (no data movement)
├─ Existing data in partition becomes exchange table
├─ Exchange table becomes new partition
└─ Duration: <1 second (metadata operation)

Note: No UNDO/REDO needed - partitions are simply swapped at metadata layer

↓
Step 3: MV REFRESH FAST (Incremental Reconstruction)
├─ REFRESH FAST mv_rebalance_summary
│  ├─ Oracle checks MV logs (change tracking)
│  ├─ Read only the new partition data
│  ├─ Apply dimension lookups
│  ├─ Incremental aggregations
│  └─ Merge with existing MV data
├─ NEW PARTITION ONLY (5M rows vs 10M+)
└─ Duration: <5 seconds (incremental only)

↓
Step 4: Cleanup
├─ TRUNCATE TABLE account_stg
└─ DROP TABLE account_fact_exch
```

**Characteristics:**
- ✓ Bulk insert (organized, no logging)
- ✓ Minimal logging (partition swap only)
- ✓ Partition-level locks (seconds only)
- ✓ MV Reconstruction is incremental (new partition only)

---

### MV Reconstruction: Full vs Incremental

#### Design 1: Full Reconstruction

```sql
-- Oracle scans the ENTIRE ACCOUNT_DAY_FCT base table
SELECT 
  snap_dt,
  rebalance_bucket,
  qlh_next_run_dt,
  COUNT(*) as account_count
FROM ACCOUNT_DAY_FCT
WHERE snap_dt >= TRUNC(SYSDATE) - 90  -- ±90 day range
GROUP BY snap_dt, rebalance_bucket, qlh_next_run_dt;
```

**Considerations:**
- Scans all 10 million rows in today's partition
- Joins to ACCOUNT_DIM (dimension lookups)
- Aggregates across all dimensions
- No incremental optimization possible
- Duration: 1-2 minutes per refresh

**SQL Execution:**
1. Full table scan of ACCOUNT_DAY_FCT (today's partition)
2. Dimension lookup for each row (or use snapshot columns)
3. GROUP BY aggregations on 10M rows
4. Replace MV contents entirely

---

#### Design 2: Incremental (FAST) Reconstruction

```sql
-- Oracle uses MV logs to find ONLY changed rows
REFRESH FAST mv_rebalance_summary;

-- Internally, Oracle performs:
-- 1. SELECT changes from MV$_LOG_ACCOUNT_DAY_FCT (new rows only)
-- 2. Dimension lookups for new rows (5M rows in new partition)
-- 3. Aggregations on deltas only
-- 4. MERGE with existing MV data
```

**Characteristics:**
- Only scans new partition data (5M rows)
- Uses MV logs to track changes
- Dimension lookups only for new/changed rows
- Incremental merge with existing aggregations
- Duration: <5 seconds per refresh

**SQL Execution:**
1. Query MV logs for changed rows (5M new rows)
2. Dimension lookup only for new rows
3. GROUP BY aggregations on deltas (5M vs 10M)
4. MERGE new aggregations with existing MV data

**Performance Impact:**
- Design 1 MV Refresh: 1-2 minutes per refresh (full scan)
- Design 2 MV Refresh: <5 seconds per refresh (incremental)
- **Benefit:** 12-24x faster MV refresh in Design 2

---

### Audit Trail Preservation

Both approaches preserve historical accuracy, just differently:

**Design 1 Approach:**
- Snapshot columns in fact table preserve dimension values at time of fact
- Changes to dimension table don't affect existing facts
- Historical queries work correctly using snapshot columns

```sql
-- Verify what investment type an account had on 2026-02-10
SELECT dim_investment_type_snap FROM ACCOUNT_DAY_FCT
WHERE account_id = 101 AND snap_dt = '2026-02-10';
-- Returns: 'ETF' (preserved in snapshot column from that date)
```

**Design 2 Approach:**
- Type 2 SCD preserves multiple versions of each dimension
- Fact table links to the dimension version valid at fact time
- Historical queries work by joining to correct dimension version

```sql
-- Verify what investment type an account had on 2026-02-10
SELECT d.investment_type FROM ACCOUNT_FACT f
JOIN ACCOUNT_DIM d ON d.account_dim_key = f.account_dim_key
WHERE f.account_number = 'A-0000123456' 
  AND f.snap_dt = '2026-02-10'
  AND d.effective_from_dt <= f.snap_dt
  AND d.effective_to_dt > f.snap_dt;
-- Returns: 'ETF' (from correct dimension version valid on that date)
```

---



### Scenario: Account Changes Investment Type Mid-Day

**Initial State (After Nightly Feed):**

| Design | Table | Key Data |
|--------|-------|----------|
| **Design 1** | ACCOUNT_DIM | `account_id=101, investment_type='ETF', dim_version=3` |
| **Design 1** | ACCOUNT_DAY_FCT | `snap_dt=2026-02-11, account_id=101, dim_investment_type_snap='ETF'` |
| **Design 2** | ACCOUNT_DIM | `account_dim_key=1001, investment_type='ETF', is_current='Y'` |
| **Design 2** | ACCOUNT_FACT | `snap_dt=2026-02-11, account_dim_key=1001` |

---

### After Intraday Update (14:30:00)

**Design 1 - Operations:**

1. ✅ Update ACCOUNT_DIM: `investment_type='STOCK', dim_version=4`
2. ✅ Update ACCOUNT_DAY_FCT: `dim_investment_type_snap='STOCK'`
3. ✅ Calculate overlay deltas
4. ✅ Insert 2 rows into SUMMARY_HOT_OVERLAY
5. ✅ Update ACCOUNT_EVENT_STATE
6. ✅ Update CDC_APPLY_STATE
7. ✅ Commit transaction

**Result Tables:**

| Table | Data |
|-------|------|
| ACCOUNT_DIM | `investment_type='STOCK', dim_version=4` (old value lost) |
| ACCOUNT_DAY_FCT | `dim_investment_type_snap='STOCK'` (snapshot preserved) |
| SUMMARY_HOT_OVERLAY | `ETF|NE|ACTIVE, 31_60_DAYS: -1`<br>`STOCK|NE|ACTIVE, 31_60_DAYS: +1` |
| ACCOUNT_EVENT_STATE | `last_event_id='IIDR-20260211-143000-001'` |

**Design 2 - Operations:**

1. ✅ Update ACCOUNT_DIM: Close row 1001 (`effective_to_dt='2026-02-11', is_current='N'`)
2. ✅ Insert ACCOUNT_DIM: New row 1002 (`investment_type='STOCK', is_current='Y'`)
3. ✅ Update ACCOUNT_FACT: `account_dim_key=1001 → 1002`
4. ✅ Commit transaction (Kafka offset auto-committed)

**Result Tables:**

| Table | Data |
|-------|------|
| ACCOUNT_DIM | Row 1001: `investment_type='ETF', effective_to_dt='2026-02-11'`<br>Row 1002: `investment_type='STOCK', effective_from_dt='2026-02-11'` |
| ACCOUNT_FACT | `account_dim_key=1002` (points to new dimension row) |

**No overlay table, no event state table needed!**

---

### Query Performance Comparison

#### Summary Query (Rebalance Buckets)

**Design 1:**
```sql
-- Query MV
SELECT * FROM mv_rebalance_summary WHERE snap_dt = '2026-02-11';
-- Query Overlay
SELECT * FROM SUMMARY_HOT_OVERLAY WHERE snap_dt = '2026-02-11';
-- Combine in application
```
**Latency:** ~150ms (MV scan + overlay scan + merge)

**Design 2:**
```sql
-- Query MV only
SELECT * FROM mv_rebalance_summary WHERE snap_dt = '2026-02-11';
```
**Latency:** ~50ms (MV scan only)

---

#### Detail Query (Filter by Investment Type)

**Design 1:**
```sql
SELECT f.*, d.account_number, d.client_name
FROM ACCOUNT_DAY_FCT f
JOIN ACCOUNT_DIM d ON d.account_id = f.account_id
WHERE f.snap_dt = '2026-02-11'
  AND f.dim_investment_type_snap = 'STOCK'  -- Filter on snapshot column
  AND f.asset_value > 200000;
```
**Latency:** ~300ms (fact scan + dimension join)

**Design 2:**
```sql
SELECT f.*, d.account_number, d.client_name, d.investment_type
FROM ACCOUNT_FACT f
JOIN ACCOUNT_DIM d ON d.account_dim_key = f.account_dim_key
WHERE f.snap_dt = '2026-02-11'
  AND d.is_current = 'Y'
  AND d.investment_type = 'STOCK'  -- Filter on dimension
  AND f.asset_value > 200000;
```
**Latency:** ~250ms (fact scan + dimension join, but simpler)

---

### Storage Comparison

**Design 1 Storage:**
- ACCOUNT_DIM: ~10M rows (one per account)
- ACCOUNT_DAY_FCT: ~10M rows/day × 180 days = 1.8B rows
- SUMMARY_HOT_OVERLAY: ~10K rows (deltas)
- ACCOUNT_EVENT_STATE: ~10M rows
- **Total:** ~1.82B rows

**Design 2 Storage:**
- ACCOUNT_DIM: ~10M rows + historical versions (~15M total with changes)
- ACCOUNT_FACT: ~10M rows/day × 180 days = 1.8B rows
- **Total:** ~1.815B rows

**Winner:** Design 2 (slightly less storage, no overlay/event state tables)

---

### Operational Complexity

**Design 1 Maintenance Tasks:**
1. Monitor overlay table size (alert if >10K rows)
2. Ensure overlay truncation after MV refresh
3. Monitor event state table for duplicates
4. Maintain Oracle Text index sync (15-30 min lag)
5. Handle overlay epoch management
6. Debug double-counting issues

**Design 2 Maintenance Tasks:**
1. Monitor MV refresh duration (alert if >30s)
2. Monitor Kafka consumer lag
3. Standard Oracle maintenance

**Winner:** Design 2 (fewer moving parts)

---

## Service Plan and Service Run (DCA/TET) in Both Designs {#service-plan-run}

Both designs support **DCA** (Dollar Cost Averaging) and **TET** (Tax-Efficient Transition) via **Plan** (enrollment/state) and **Run** (each execution) tables. How they are modeled, updated, and used in MVs differs.

### Are They in Both Designs?

| Concept | Design 1 (Main v5) | Design 2 (Gilfoyle) |
|--------|--------------------|---------------------|
| **Plan table** | ACCOUNT_SERVICE_PLAN | SERVICE_PLAN |
| **Run table** | ACCOUNT_SERVICE_RUN | SERVICE_RUN |
| **Optional schedule** | ACCOUNT_SERVICE_SCHEDULE | Not in schema (can be added) |
| **In fact table** | Denormalized: dca_plan_status, tet_plan_status, dca_next_due_dt, tet_next_due_dt in ACCOUNT_DAY_FCT | No; DCA/TET come from PLAN/RUN only |

**Summary:** Both designs have PLAN and RUN. Design 1 also copies DCA/TET *state* into the daily fact for fast filters and for MVs that are built from the fact. Design 2 keeps DCA/TET only in SERVICE_PLAN and SERVICE_RUN; KPIs are queried from those tables (and optionally from MVs if built on them).

---

### Design 1: PLAN/RUN and How They Are Updated

#### Tables

- **ACCOUNT_SERVICE_PLAN** – One row per account + service (DCA or TET): enrollment, status, next_due_dt, last_run_dt, expected_complete_dt, etc.
- **ACCOUNT_SERVICE_RUN** – Append-only: one row per execution (run_dt, run_status, amount, source_event_id for idempotency).
- **ACCOUNT_DAY_FCT** – Also holds **denormalized** DCA/TET state: dca_plan_status, dca_next_due_dt, tet_plan_status, tet_next_due_dt, tet_expected_complete_dt (for today’s snapshot and fast filters).

#### Nightly load impact

1. **Staging:** Bulk feed includes plan and run data (or derived from source).
2. **ACCOUNT_SERVICE_PLAN:** MERGE (Type 1) from staging: update existing plans, insert new. Sets status, next_due_dt, last_run_dt, expected_complete_dt.
3. **ACCOUNT_SERVICE_RUN:** Bulk insert new runs (e.g. completed executions since last run). Idempotency by source_event_id if present.
4. **ACCOUNT_DAY_FCT:** When building today’s partition (or MERGE), fact rows are updated with dca_plan_status, dca_next_due_dt, tet_plan_status, tet_next_due_dt from PLAN (and SCHEDULE if used) so the fact has a consistent “as of today” snapshot.
5. **MVs:** mv_rebalance_summary and mv_qlh_weekly are built from **ACCOUNT_DAY_FCT** (and snapshot columns). They do **not** join to ACCOUNT_SERVICE_PLAN/RUN. So DCA/TET *summary* counts (e.g. “DCA enrolled”, “DCA completed last 30 days”) are either:
   - Queried **directly** from ACCOUNT_SERVICE_PLAN and ACCOUNT_SERVICE_RUN, or
   - Reflected indirectly if the UI summary uses fact snapshot columns that were populated from PLAN.

#### Intraday impact

1. **CDC:** Messages can carry plan changes (enrollment, status, next due) and new run events.
2. **ACCOUNT_SERVICE_PLAN:** MERGE on plan_id or (account_id, service_type). Update status, next_due_dt, last_run_dt.
3. **ACCOUNT_SERVICE_RUN:** INSERT new run rows (append-only). Idempotency via source_event_id.
4. **ACCOUNT_DAY_FCT:** Today’s row for the account is updated with new dca_plan_status, dca_next_due_dt, tet_plan_status, tet_next_due_dt (and tet_expected_complete_dt if applicable).
5. **Overlay:** If summary buckets depend on DCA/TET state, overlay deltas are computed and SUMMARY_HOT_OVERLAY is updated.
6. **MV refresh:** REFRESH COMPLETE (or partition-scoped COMPLETE) for mv_rebalance_summary and mv_qlh_weekly runs on a schedule (e.g. 15–30 min). Those MVs are **reconstructed from ACCOUNT_DAY_FCT** (and snapshot columns), not from PLAN/RUN. So when PLAN/RUN (and thus fact snapshot columns) change, the next MV refresh picks up the new state. No separate “DCA/TET MV” is required unless you add one.

---

### Design 2: PLAN/RUN and How They Are Updated

#### Tables

- **SERVICE_PLAN** – One row per account + service type (DCA/TET): enrolled_dt, status, expected_completion, withdrawal_frequency/amount (DCA), target_gains/losses (TET).
- **SERVICE_RUN** – Append-only: one row per execution (run_dt, run_status, amount_processed, gains_harvested, losses_harvested). Partitioned by run_dt (e.g. monthly).

#### Nightly load impact

1. **Staging:** Bulk feed includes plan and run data.
2. **SERVICE_PLAN:** MERGE on (account_number, service_type). Update status, expected_completion, withdrawal_*, etc. No separate “fact snapshot” for DCA/TET; PLAN is the source of truth.
3. **SERVICE_RUN:** Bulk insert new runs. Idempotency by business key or source id if provided.
4. **ACCOUNT_FACT:** Built from staging (e.g. partition exchange). Does **not** store DCA/TET state; it has rebalance_dt, qlh_* only. So nightly batch does **not** update ACCOUNT_FACT with PLAN columns.
5. **MVs:** mv_rebalance_summary and mv_qlh_weekly are built from **ACCOUNT_FACT + ACCOUNT_DIM** only. They do **not** include DCA/TET. So:
   - **DCA/TET KPIs** (enrolled counts, completed last 30 days, YTD, next 12 months) are queried **directly** from SERVICE_PLAN and SERVICE_RUN (see Gilfoyle Appendix A.1, A.2).
   - If you add **DCA/TET summary MVs** (e.g. mv_dca_summary, mv_tet_summary), they would be based on SERVICE_PLAN and SERVICE_RUN. Those MVs would need to be refreshed when PLAN or RUN change (see below).

#### Intraday impact

1. **CDC:** Plan updates (status, dates) and new run events.
2. **SERVICE_PLAN:** MERGE (or UPDATE/INSERT) by (account_number, service_type).
3. **SERVICE_RUN:** INSERT new run rows (append-only). Idempotency as with nightly.
4. **ACCOUNT_FACT:** No DCA/TET columns; no update to fact for plan/run changes.
5. **MV refresh:** REFRESH FAST for mv_rebalance_summary and mv_qlh_weekly runs on schedule (e.g. every 5 min). They are **not** based on PLAN/RUN, so PLAN/RUN changes do **not** trigger or affect these MVs. Only if you introduce MVs on SERVICE_PLAN/SERVICE_RUN do those need to be refreshed when PLAN/RUN change.

---

### How MVs Are Based on PLAN/RUN (and When They Need Refresh)

| MV / KPI | Design 1 | Design 2 |
|----------|----------|----------|
| **mv_rebalance_summary** | From ACCOUNT_DAY_FCT (snapshot columns). No join to PLAN/RUN. | From ACCOUNT_FACT + ACCOUNT_DIM. No PLAN/RUN. |
| **mv_qlh_weekly** | From ACCOUNT_DAY_FCT (qlh_*). No PLAN/RUN. | From ACCOUNT_FACT + ACCOUNT_DIM (qlh_*). No PLAN/RUN. |
| **DCA enrolled count** | Direct query on ACCOUNT_SERVICE_PLAN, or from fact snapshot if UI uses it. | Direct query on SERVICE_PLAN (e.g. Appendix A.2). |
| **DCA completed last 30 days** | Direct query on ACCOUNT_SERVICE_RUN (run_dt, run_status). | Direct query on SERVICE_RUN (Appendix A.1). |
| **TET completed YTD** | Direct query on ACCOUNT_SERVICE_RUN. | Direct query on SERVICE_RUN. |
| **TET expected completion next 12 months** | From ACCOUNT_SERVICE_PLAN or fact column tet_expected_complete_dt. | From SERVICE_PLAN.expected_completion. |

So in both designs, the **rebalance and QLH MVs** are **not** built from PLAN/RUN. They are reconstructed (Design 1: COMPLETE from fact; Design 2: FAST from fact + dimension) on their normal schedule. PLAN and RUN are updated by nightly and intraday flows; if you add **separate DCA/TET MVs** (e.g. on SERVICE_PLAN/SERVICE_RUN), then:

- **Design 1:** You could base a DCA/TET MV on ACCOUNT_DAY_FCT (using dca_plan_status, tet_plan_status, etc.) and refresh it with the same COMPLETE refresh as the other MVs; or base it on ACCOUNT_SERVICE_PLAN/RUN and add MV logs on those tables for FAST refresh.
- **Design 2:** You would add MV logs on SERVICE_PLAN and SERVICE_RUN and define MVs on those tables; REFRESH FAST when PLAN or RUN change (e.g. same 5‑minute schedule or after CDC batch).

---

### Summary: Nightly and Intraday Impact on PLAN/RUN

| Event | Design 1 | Design 2 |
|-------|----------|----------|
| **Nightly: PLAN** | MERGE ACCOUNT_SERVICE_PLAN from staging; update today’s fact snapshot columns (dca_*, tet_*) from PLAN. | MERGE SERVICE_PLAN from staging. No fact columns for DCA/TET. |
| **Nightly: RUN** | Bulk insert into ACCOUNT_SERVICE_RUN (new runs). | Bulk insert into SERVICE_RUN. |
| **Nightly: MVs** | REFRESH COMPLETE mv_rebalance_summary, mv_qlh_weekly (from fact only). DCA/TET KPIs from direct queries on PLAN/RUN. | REFRESH FAST same MVs (from fact+dim). DCA/TET KPIs from direct queries on PLAN/RUN. |
| **Intraday: PLAN** | CDC MERGE into ACCOUNT_SERVICE_PLAN; update today’s fact row (dca_*, tet_*); overlay deltas if needed. | CDC MERGE into SERVICE_PLAN. No fact update. |
| **Intraday: RUN** | CDC INSERT into ACCOUNT_SERVICE_RUN (idempotent); no direct change to fact unless you derive next_due from runs. | CDC INSERT into SERVICE_RUN. No fact update. |
| **Intraday: MVs** | REFRESH COMPLETE on schedule; MVs built from fact, so updated fact snapshot columns are reflected after refresh. | REFRESH FAST on schedule; MVs unchanged by PLAN/RUN. Any DCA/TET MVs would need their own refresh if implemented. |

---

## Kafka Reliability: Can We Rely on It When Interacting with the DB? {#kafka-reliability}

Design 2 relies on **Kafka "exactly-once" semantics** to avoid manual idempotency tables (ACCOUNT_EVENT_STATE, CDC_APPLY_STATE). Design 1 assumes **at-least-once** and defends with idempotent MERGEs and explicit state tracking. Whether Kafka can be "relied upon that much" depends on what you mean by exactly-once and what safeguards you keep.

### What Design 2 Actually Relies On

- **Transactional consumer:** Offset commit is tied to the same logical transaction as the DB write (e.g. DB commit then Kafka offset commit in one coordinated step, or via a transaction manager that coordinates both).
- **read_committed:** Consumer only sees committed producer transactions, reducing duplicates from the producer side.
- **No manual idempotency table:** The design assumes that once the DB transaction commits, the framework will commit the offset, so the same message will not be processed again.

So Design 2 relies on: (1) Kafka + framework correctly implementing transactional consume and offset commit, and (2) no duplicate delivery in the window between DB commit and offset commit (e.g. crash, rebalance).

### Can Kafka Be Relied Upon That Much?

**Short answer:** It depends on your environment and how much risk you accept. In practice, many teams **do not rely on Kafka alone** for correctness when writing to a database; they add **defense in depth**.

| Aspect | Reality | Implication |
|--------|--------|-------------|
| **Kafka's native guarantee** | At-least-once (or at-most-once). "Exactly-once" is *processing* semantics when using transactions + coordinated commit. | You depend on the whole chain: producer transactions, consumer transactions, and offset commit tied to DB commit. |
| **Transactional consumer + DB** | Requires a transaction manager that can coordinate Kafka offset commit with the DB transaction (e.g. commit DB, then commit offset in same "logical" transaction). Spring Kafka can support this, but the exact setup (and support for Oracle) must be verified. | Not all stacks support true "DB + Kafka in one transaction"; some only approximate it (e.g. commit DB first, then offset; crash after DB commit = replay risk). |
| **Failures** | Consumer crash after DB commit but before offset commit → message is redelivered → duplicate processing unless the DB write is idempotent. Rebalances and broker issues can also cause redelivery. | Even with "exactly-once" config, **idempotent writes in the DB** are the only way to be sure duplicates don't corrupt data. |
| **Upstream (IIDR)** | CDC source might send duplicate events (e.g. retries, reconnects). | Again, idempotency in the consumer (by key/event_id) is the safe approach. |

So: **Kafka can be relied upon for ordering and durability**, but for **"process exactly once when writing to the DB"** the robust approach is to **combine** Kafka's semantics with **idempotent database operations**.

### Recommendation: Don't Rely on Kafka Alone; Keep the DB Idempotent

Even if you adopt Design 2 and use Kafka's transactional/exactly-once features:

1. **Make DB writes idempotent**
   - **Dimension / fact:** MERGE (or upsert) by business key (e.g. account_number, snap_dt). Processing the same event twice should produce the same final row.
   - **SERVICE_RUN (and similar):** Use a unique constraint on `source_event_id` (or equivalent) and ignore duplicate key on insert, so replays don't create duplicate run rows.

2. **Optional: light-weight idempotency in the DB**
   - If you want to avoid duplicate work (e.g. repeated MERGEs for the same event), you can keep a **small idempotency table** (e.g. last N event_ids or a cache) and skip processing when the event_id was already applied. This is "optional" for correctness if MERGE/upsert and RUN inserts are already idempotent, but it can reduce load and complexity in overlay logic.

3. **Verify your stack**
   - Confirm that Spring Kafka (or your consumer framework) actually coordinates **Oracle transaction commit** with **Kafka offset commit** in the way Design 2 assumes (e.g. no commit of offset before DB commit, and no double commit under failure). If not, you effectively have at-least-once and **must** rely on idempotent DB writes.

### Design 1 vs Design 2: How Much They Rely on Kafka

| | Design 1 (Main v5) | Design 2 (Gilfoyle) |
|--|--------------------|----------------------|
| **Assumption** | At-least-once delivery | Exactly-once *processing* (with transactional consumer) |
| **Idempotency** | Explicit: ACCOUNT_EVENT_STATE, overlay dedupe, idempotent MERGE | Implicit: MERGE/upsert by key; optional source_event_id on RUN |
| **If Kafka redelivers** | Handled by event state check + idempotent MERGE; overlay dedupe prevents double-counting. | Safe **only if** MERGE/inserts are idempotent by key/event_id. |
| **If offset commit fails after DB commit** | Replay; event state + idempotent MERGE make it safe. | Replay; safe only if DB writes are idempotent. |

So: **Design 1 explicitly assumes Kafka is not "exactly-once"** and builds idempotency and dedupe into the schema and flow. **Design 2 assumes the framework gives exactly-once** but is **only as reliable as the DB writes are idempotent** when the assumption fails (redelivery, crash, or misconfiguration).

### Bottom Line

- **Can Kafka be relied upon "that much" when interacting with the DB?**  
  - For **ordering and durability**, yes, within normal Kafka guarantees.  
  - For **no duplicate processing**, only if your **consumer + DB** stack truly implements transactional consume and offset commit **and** you have verified it. In practice, **relying on Kafka alone** for "exactly once" is risky; the safe approach is to **always make DB writes idempotent** (MERGE by key, unique event_id on RUN) and treat Kafka as at-least-once. Then Design 2's "no manual idempotency table" is a **simplification of the flow**, not a bet that Kafka will never redeliver.

- **Recommendation:** Use Design 2's simpler flow (single transaction, no overlay) but **still** design the DB layer for at-least-once: idempotent MERGEs, optional source_event_id dedupe for RUN, and validation that your Kafka–Oracle integration really commits offsets only after a successful DB commit. That way you get Design 2's simplicity without over-relying on Kafka when interacting with the DB.

---

## Conclusion and Recommendation {#conclusion}

### Summary of Differences

| Aspect | Design 1 (Main v5) | Design 2 (Gilfoyle Revised) |
|--------|-------------------|----------------------------|
| **Permanent Tables** | 11+ tables | 6 tables (45% reduction) |
| **Staging Tables** | ACCOUNT_STG (temporary) | ACCOUNT_STG + account_fact_exch (temporary) |
| **Operations per CDC** | 7 operations | 1 transaction (85% reduction) |
| **Historical Tracking** | Snapshot columns | Type 2 SCD (industry standard) |
| **Summary Freshness** | 15-30 min + overlay | 5 min FAST refresh |
| **Name Search** | Oracle Text (15-30 min sync) | Function-based index (real-time) |
| **Idempotency** | Manual (2 state tables) | Kafka framework |
| **Complexity** | High (custom overlay logic) | Medium (standard patterns) |
| **Nightly Batch Strategy** | MERGE into partitions | Partition exchange (faster) |

### Recommendation: **Design 2 (Gilfoyle Revised)**

**Why Design 2 is Better:**

1. **Simpler Architecture:** 45% fewer tables means less code to maintain
2. **Better Performance:** 85% fewer database operations per update
3. **Standard Patterns:** Type 2 SCD is a well-understood industry pattern
4. **Faster Freshness:** 5-minute MV refresh vs 15-30 minutes + overlay
5. **Framework-Managed:** Kafka handles idempotency automatically
6. **Easier Onboarding:** New developers understand Type 2 SCD immediately

**When Design 1 Might Be Preferred:**
- If you have existing Type 1 SCD infrastructure
- If snapshot columns are required by business rules
- If overlay table provides specific business value

**Final Verdict:** Design 2 (Gilfoyle Revised) meets all requirements with significantly less complexity and better long-term maintainability.

---

## Appendix: Key SQL Patterns

### Design 1: Snapshot Column Pattern
```sql
-- Fact table stores copies of dimension values
CREATE TABLE account_day_fct (
  snap_dt DATE,
  account_id NUMBER,
  asset_value NUMBER,
  dim_investment_type_snap VARCHAR2(50),  -- Snapshot column
  dim_status_snap VARCHAR2(50),           -- Snapshot column
  ...
);
```

### Design 2: Type 2 SCD Pattern
```sql
-- Dimension table stores versions with effective dating
CREATE TABLE account_dim (
  account_dim_key NUMBER PRIMARY KEY,
  account_number VARCHAR2(50),
  investment_type VARCHAR2(50),
  effective_from_dt DATE,
  effective_to_dt DATE DEFAULT DATE '9999-12-31',
  is_current CHAR(1) DEFAULT 'Y'
);

-- Fact table links to dimension version
CREATE TABLE account_fact (
  snap_dt DATE,
  account_number VARCHAR2(50),
  account_dim_key NUMBER REFERENCES account_dim(account_dim_key),
  asset_value NUMBER,
  ...
);
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-16  
**Author:** Technical Analysis Team
