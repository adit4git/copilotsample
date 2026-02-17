# ADR-012: Data Flow Timeline Diagrams
## Visual Representation of Data Processing Lifecycle

**Document Purpose:** This document provides visual flow diagrams showing the complete data lifecycle from nightly feed through intraday updates, MV refreshes, and UI queries for both design approaches.

---

## Table of Contents

1. [Design 1: Main Design (v5) - Complete Timeline](#design-1-timeline)
2. [Design 2: Gilfoyle Revised - Complete Timeline](#design-2-timeline)
3. [Side-by-Side Timeline Comparison](#timeline-comparison)
4. [Partition Exchange vs Full Merge: Nightly Update Comparison](#partition-exchange-comparison)
5. [Detailed Flow Diagrams](#detailed-flows)

---

## Design 1: Main Design (v5) - Complete Timeline {#design-1-timeline}

### 24-Hour Timeline Overview

```mermaid
gantt
    title Design 1: 24-Hour Data Processing Timeline
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Nightly Batch
    Bulk Feed Arrival           :00:00, 30m
    Staging Load                :00:30, 30m
    Validation & Deduplication  :01:00, 30m
    Dimension Updates (Type 1)  :01:30, 30m
    Fact Table Updates          :02:00, 30m
    MV Refresh (COMPLETE)       :02:30, 2h
    Overlay Truncate            :04:30, 5m
    Cleanup                     :04:35, 5m
    
    section Intraday Processing
    CDC Messages Arrive         :08:00, 12h
    Micro-batch Processing       :08:00, 12h
    Overlay Updates              :08:00, 12h
    
    section MV Refresh Cycle
    MV Refresh #1 (15 min)      :08:15, 2m
    MV Refresh #2 (30 min)      :08:30, 2m
    MV Refresh #3 (45 min)      :08:45, 2m
    MV Refresh #4 (60 min)      :09:00, 2m
    MV Refresh Continues...      :09:00, 11h
    
    section UI Queries
    Summary Grid Queries        :08:00, 12h
    Detail Grid Queries         :08:00, 12h
```

---

### Detailed Data Flow: Nightly Batch Process

```mermaid
flowchart TD
    Start([Nightly Batch Starts<br/>23:00]) --> BulkFeed[Bulk Feed File Arrives<br/>~10M accounts]
    
    BulkFeed --> Stage1[Load to Staging Tables<br/>ACCOUNT_STG]
    
    Stage1 --> Validate[Validate & Deduplicate<br/>Business Rules Check]
    
    Validate --> DimUpdate[Update ACCOUNT_DIM<br/>Type 1 MERGE<br/>Overwrite Current Values<br/>Increment dim_version]
    
    DimUpdate --> CalcDerived[Calculate Derived Fields<br/>QLH next_run_dt<br/>Rebalance buckets]
    
    CalcDerived --> FactMerge["Full Merge Update<br/>ACCOUNT_DAY_FCT<br/>MERGE with snapshot columns<br/>Copy dim_*_snap values<br/>(Design 1 Approach)"]
    
    FactMerge --> MVReconstruction[MV Reconstruction<br/>Scan entire ACCOUNT_DAY_FCT<br/>FROM statement on base table<br/>Aggregate all dimensions<br/>Group by rebalance/qlh buckets]
    
    MVReconstruction --> MVRefresh[REFRESH COMPLETE<br/>mv_rebalance_summary<br/>mv_qlh_weekly<br/>Duration: 1-2 minutes]
    
    MVRefresh --> OverlayTruncate[TRUNCATE<br/>SUMMARY_HOT_OVERLAY<br/>Clear all deltas]
    
    OverlayTruncate --> EventStateClear[Clear/Archive<br/>ACCOUNT_EVENT_STATE<br/>Old event tracking]
    
    EventStateClear --> Cleanup[Drop Staging Tables<br/>Archive Logs]
    
    Cleanup --> End([Batch Complete<br/>02:35])
    
    style Start fill:#0277bd,color:#fff
    style End fill:#2e7d32,color:#fff
    style MVRefresh fill:#f57f17,color:#fff
    style MVReconstruction fill:#c62828,color:#fff
    style FactMerge fill:#1b5e20,color:#fff
    style OverlayTruncate fill:#e64a19,color:#fff
```

---

### Detailed Data Flow: Intraday CDC Processing

```mermaid
sequenceDiagram
    participant IIDR as IIDR Source
    participant Kafka as Kafka Topic
    participant Consumer as Spring Batch Consumer
    participant DB as Oracle Database
    participant MV as Materialized Views
    participant UI as UI Dashboard
    
    Note over IIDR,UI: Intraday Processing (08:00 - 20:00)
    
    IIDR->>Kafka: CDC Message<br/>account_id=101<br/>investment_type: ETF→STOCK<br/>event_id: IIDR-001
    
    Kafka->>Consumer: Consume Message<br/>Micro-batch (100-500 msgs)
    
    Consumer->>DB: 1. Check ACCOUNT_EVENT_STATE<br/>Is event_id already processed?
    
    alt Event Not Processed
        Consumer->>DB: 2. UPDATE ACCOUNT_DIM<br/>investment_type='STOCK'<br/>dim_version++
        
        Consumer->>DB: 3. MERGE ACCOUNT_DAY_FCT<br/>Update today's row<br/>dim_investment_type_snap='STOCK'
        
        Consumer->>DB: 4. Calculate Overlay Deltas<br/>Old bucket: -1<br/>New bucket: +1
        
        Consumer->>DB: 5. INSERT SUMMARY_HOT_OVERLAY<br/>Two delta rows
        
        Consumer->>DB: 6. UPDATE ACCOUNT_EVENT_STATE<br/>Record event_id processed
        
        Consumer->>DB: 7. UPDATE CDC_APPLY_STATE<br/>Commit Kafka offset
        
        DB-->>Consumer: Transaction Committed
    else Event Already Processed
        Consumer->>DB: Skip (Idempotency)
        DB-->>Consumer: No-op
    end
    
    Note over MV: MV Refresh Scheduled<br/>Every 15-30 minutes
    
    MV->>DB: REFRESH COMPLETE<br/>mv_rebalance_summary
    
    DB->>MV: Rebuild Aggregations<br/>From ACCOUNT_DAY_FCT
    
    MV->>DB: TRUNCATE SUMMARY_HOT_OVERLAY<br/>Clear deltas after refresh
    
    UI->>DB: Query Summary Grid<br/>SELECT FROM mv + overlay
    
    DB-->>UI: Return Combined Results<br/>MV counts + overlay deltas
```

---

### State Transitions: Before/After Nightly Update

```mermaid
stateDiagram-v2
    [*] --> PreNightly
    
    PreNightly: Pre-Nightly State
    note right of PreNightly
        ACCOUNT_DIM: Current values
        ACCOUNT_DAY_FCT: Yesterday's data
        MV: Stale (yesterday's data)
        Overlay: Accumulated deltas
    end note
    
    PreNightly --> NightlyProcessing
    
    NightlyProcessing: Nightly Processing
    note right of NightlyProcessing
        Load staging
        Update dimensions
        Update facts
        Refresh MVs
    end note
    
    NightlyProcessing --> PostNightly
    
    PostNightly: Post-Nightly State
    note right of PostNightly
        ACCOUNT_DIM: Updated
        ACCOUNT_DAY_FCT: Today's snapshot
        MV: Fresh (today's data)
        Overlay: Empty
    end note
    
    PostNightly --> Intraday
    
    Intraday: Intraday Updates
    note right of Intraday
        CDC messages arrive
        Update DIM/FACT
        Accumulate overlay deltas
        MV refreshes every 15-30 min
    end note
    
    Intraday --> MVRefresh
    
    MVRefresh: MV Refresh
    note right of MVRefresh
        Rebuild aggregations
        Truncate overlay
    end note
    
    MVRefresh --> Intraday
    
    Intraday --> PreNightly
```

---

### Data State at Key Timestamps

#### T-0: Before Nightly Update (22:59:59)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM"
        D1["account_id: 101<br/>investment_type: ETF<br/>dim_version: 3"]
    end
    
    subgraph "ACCOUNT_DAY_FCT"
        F1["snap_dt: 2026-02-10<br/>account_id: 101<br/>dim_investment_type_snap: ETF"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M1["snap_dt: 2026-02-10<br/>ETF_31_60_DAYS: 2300"]
    end
    
    subgraph "SUMMARY_HOT_OVERLAY"
        O1["ETF_NE_ACTIVE<br/>31_60_DAYS: +5<br/>0_30_DAYS: -3"]
    end
    
    D1 --> F1
    F1 --> M1
    O1 -.->|Deltas| M1
    style D1 fill:#0277bd,color:#fff
    style F1 fill:#1b5e20,color:#fff
    style M1 fill:#f57f17,color:#fff
    style O1 fill:#c62828,color:#fff
```

#### T+1: After Nightly Update (02:35:00)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM"
        D2["account_id: 101<br/>investment_type: ETF<br/>dim_version: 3<br/>Updated: 02:00"]
    end
    
    subgraph "ACCOUNT_DAY_FCT"
        F2["snap_dt: 2026-02-11<br/>account_id: 101<br/>dim_investment_type_snap: ETF<br/>asset_value: 255000"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M2["snap_dt: 2026-02-11<br/>ETF_31_60_DAYS: 2299<br/>Fresh from MV refresh"]
    end
    
    subgraph "SUMMARY_HOT_OVERLAY"
        O2["EMPTY<br/>Truncated after MV refresh"]
    end
    
    D2 --> F2
    F2 --> M2
    style D2 fill:#0277bd,color:#fff
    style F2 fill:#1b5e20,color:#fff
    style M2 fill:#f57f17,color:#fff
    style O2 fill:#e64a19,color:#fff
```

#### T+2: After Intraday Update (14:30:05)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM"
        D3["account_id: 101<br/>investment_type: STOCK<br/>dim_version: 4<br/>Updated: 14:30"]
    end
    
    subgraph "ACCOUNT_DAY_FCT"
        F3["snap_dt: 2026-02-11<br/>account_id: 101<br/>dim_investment_type_snap: STOCK<br/>Updated: 14:30"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M3["snap_dt: 2026-02-11<br/>ETF_31_60_DAYS: 2299<br/>STOCK_31_60_DAYS: 1800<br/>Last refresh: 14:00"]
    end
    
    subgraph "SUMMARY_HOT_OVERLAY"
        O3["ETF_NE_ACTIVE<br/>31_60_DAYS: -1<br/>STOCK_NE_ACTIVE<br/>31_60_DAYS: +1<br/>Updated: 14:30"]
    end
    
    D3 --> F3
    F3 --> M3
    O3 -.->|Deltas| M3
    style D3 fill:#0277bd,color:#fff
    style F3 fill:#1b5e20,color:#fff
    style M3 fill:#b71c1c,color:#fff
    style O3 fill:#ff6f00,color:#fff
```

#### T+3: After MV Refresh (14:32:00)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM"
        D4["account_id: 101<br/>investment_type: STOCK<br/>dim_version: 4"]
    end
    
    subgraph "ACCOUNT_DAY_FCT"
        F4["snap_dt: 2026-02-11<br/>account_id: 101<br/>dim_investment_type_snap: STOCK"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M4["snap_dt: 2026-02-11<br/>ETF_31_60_DAYS: 2298<br/>STOCK_31_60_DAYS: 1801<br/>Refreshed: 14:32"]
    end
    
    subgraph "SUMMARY_HOT_OVERLAY"
        O4["EMPTY<br/>Truncated after refresh"]
    end
    
    D4 --> F4
    F4 --> M4
    style D4 fill:#0277bd,color:#fff
    style F4 fill:#1b5e20,color:#fff
    style O4 fill:#e64a19,color:#fff
    style M4 fill:#2e7d32,color:#fff
```

---

## Design 2: Gilfoyle Revised - Complete Timeline {#design-2-timeline}

### 24-Hour Timeline Overview

```mermaid
gantt
    title Design 2: 24-Hour Data Processing Timeline
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Nightly Batch
    Bulk Feed Arrival           :00:00, 30m
    Staging Load                :00:30, 30m
    Validation & Deduplication  :01:00, 30m
    Dimension Updates (Type 2)  :01:30, 30m
    Fact Table Updates          :02:00, 30m
    MV Refresh (FAST)           :02:30, 5m
    Cleanup                     :02:35, 5m
    
    section Intraday Processing
    CDC Messages Arrive         :08:00, 12h
    Transaction Processing       :08:00, 12h
    
    section MV Refresh Cycle
    MV Refresh #1 (5 min)       :08:05, 3s
    MV Refresh #2 (10 min)      :08:10, 3s
    MV Refresh #3 (15 min)      :08:15, 3s
    MV Refresh #4 (20 min)      :08:20, 3s
    MV Refresh Continues...     :08:20, 11h40m
    
    section UI Queries
    Summary Grid Queries         :08:00, 12h
    Detail Grid Queries         :08:00, 12h
```

---

### Detailed Data Flow: Nightly Batch Process

```mermaid
flowchart TD
    Start([Nightly Batch Starts<br/>23:00]) --> BulkFeed[Bulk Feed File Arrives<br/>~10M accounts]
    
    BulkFeed --> Stage1[Load to Staging Tables<br/>ACCOUNT_STG]
    
    Stage1 --> Validate[Validate & Deduplicate<br/>Business Rules Check]
    
    Validate --> DimCheck{Check Dimension<br/>Changes}
    
    DimCheck -->|New Account| DimInsert[INSERT ACCOUNT_DIM<br/>New Type 2 row<br/>effective_from_dt = today<br/>is_current = 'Y']
    
    DimCheck -->|Changed Attributes| DimClose[UPDATE ACCOUNT_DIM<br/>Close current row<br/>effective_to_dt = today<br/>is_current = 'N']
    
    DimClose --> DimInsertNew[INSERT ACCOUNT_DIM<br/>New Type 2 row<br/>effective_from_dt = today<br/>is_current = 'Y']
    
    DimInsert --> BuildExchange[Build Exchange Partition<br/>CREATE TABLE account_fact_exch<br/>AS SELECT from ACCOUNT_STG<br/>JOIN ACCOUNT_DIM]
    
    DimInsertNew --> BuildExchange
    
    BuildExchange --> ExchangePart["Partition Exchange<br/>ALTER TABLE EXCHANGE PARTITION<br/>Instant metadata operation<br/>No data movement<br/>(Design 2 Approach)"]
    
    ExchangePart --> MVReconstruction[MV Reconstruction<br/>Scan partitioned ACCOUNT_FACT<br/>Read new partition FROM<br/>Aggregate by dimensions<br/>Update MV logs]
    
    MVReconstruction --> MVRefresh[REFRESH FAST<br/>mv_rebalance_summary<br/>mv_qlh_weekly<br/>Duration: <5 seconds]
    
    MVRefresh --> Cleanup[TRUNCATE ACCOUNT_STG<br/>DROP account_fact_exch<br/>Archive Logs]
    
    Cleanup --> End([Batch Complete<br/>02:35])
    
    style Start fill:#0277bd,color:#fff
    style End fill:#2e7d32,color:#fff
    style MVRefresh fill:#2e7d32,color:#fff
    style MVReconstruction fill:#c62828,color:#fff
    style ExchangePart fill:#0277bd,color:#fff
    style DimInsert fill:#f57f17,color:#fff
    style DimInsertNew fill:#f57f17,color:#fff
    style BuildExchange fill:#0277bd,color:#fff
```

---

### Detailed Data Flow: Intraday CDC Processing

```mermaid
sequenceDiagram
    participant IIDR as IIDR Source
    participant Kafka as Kafka Topic<br/>(Exactly-Once)
    participant Consumer as Spring Batch Consumer<br/>(Transactional)
    participant DB as Oracle Database
    participant MV as Materialized Views
    participant UI as UI Dashboard
    
    Note over IIDR,UI: Intraday Processing (08:00 - 20:00)
    
    IIDR->>Kafka: CDC Message<br/>account_number=A-0000123456<br/>investment_type: ETF→STOCK<br/>event_id: IIDR-001
    
    Kafka->>Consumer: Consume Message<br/>Micro-batch (100-500 msgs)
    
    Note over Consumer,DB: Single Transaction Begins
    
    Consumer->>DB: 1. UPDATE ACCOUNT_DIM<br/>Close current row<br/>effective_to_dt = today<br/>is_current = 'N'
    
    Consumer->>DB: 2. INSERT ACCOUNT_DIM<br/>New row<br/>investment_type='STOCK'<br/>effective_from_dt = today<br/>is_current = 'Y'
    
    Consumer->>DB: 3. UPDATE ACCOUNT_FACT<br/>Set account_dim_key<br/>to new dimension key<br/>for snap_dt >= today
    
    Consumer->>DB: COMMIT Transaction
    
    DB-->>Consumer: Transaction Committed
    
    Note over Kafka: Kafka Offset<br/>Auto-Committed<br/>(Exactly-Once)
    
    Note over MV: MV Refresh Scheduled<br/>Every 5 minutes
    
    MV->>DB: REFRESH FAST<br/>mv_rebalance_summary<br/>(Incremental)
    
    DB->>MV: Update Aggregations<br/>From MV Logs Only<br/>Duration: <5 seconds
    
    UI->>DB: Query Summary Grid<br/>SELECT FROM mv_rebalance_summary
    
    DB-->>UI: Return Results<br/>(No overlay needed)
```

---

### State Transitions: Before/After Nightly Update

```mermaid
stateDiagram-v2
    [*] --> PreNightly
    
    PreNightly: Pre-Nightly State
    note right of PreNightly
        ACCOUNT_DIM: Current + historical rows
        ACCOUNT_FACT: Yesterday's data
        MV: Stale (yesterday's data)
    end note
    
    PreNightly --> NightlyProcessing
    
    NightlyProcessing: Nightly Processing
    note right of NightlyProcessing
        Load staging
        Type 2 dimension updates
        Update facts with FK links
        FAST refresh MVs
    end note
    
    NightlyProcessing --> PostNightly
    
    PostNightly: Post-Nightly State
    note right of PostNightly
        ACCOUNT_DIM: Updated with new versions
        ACCOUNT_FACT: Today's snapshot
        MV: Fresh (FAST refresh <5s)
    end note
    
    PostNightly --> Intraday
    
    Intraday: Intraday Updates
    note right of Intraday
        CDC messages arrive
        Single transaction updates
        MV FAST refresh every 5 min
    end note
    
    Intraday --> MVRefresh
    
    MVRefresh: FAST MV Refresh
    note right of MVRefresh
        Incremental update
        <5 seconds duration
    end note
    
    MVRefresh --> Intraday
    
    Intraday --> PreNightly
```

---

### Data State at Key Timestamps

#### T-0: Before Nightly Update (22:59:59)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM (Type 2)"
        D1["account_dim_key: 1001<br/>account_number: A-0000123456<br/>investment_type: ETF<br/>effective_from: 2025-01-01<br/>effective_to: 9999-12-31<br/>is_current: Y"]
    end
    
    subgraph "ACCOUNT_FACT"
        F1["snap_dt: 2026-02-10<br/>account_number: A-0000123456<br/>account_dim_key: 1001<br/>asset_value: 250000"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M1["snap_dt: 2026-02-10<br/>ETF_31_60_DAYS: 2300<br/>Last refresh: 02:30"]
    end
    
    D1 -->|FK Link| F1
    F1 --> M1
    style D1 fill:#0277bd,color:#fff
    style F1 fill:#1b5e20,color:#fff
    style M1 fill:#f57f17,color:#fff
```

#### T+1: After Nightly Update (02:35:00)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM (Type 2)"
        D2["account_dim_key: 1001<br/>investment_type: ETF<br/>effective_to: 9999-12-31<br/>is_current: Y<br/>No changes today"]
    end
    
    subgraph "ACCOUNT_FACT"
        F2["snap_dt: 2026-02-11<br/>account_number: A-0000123456<br/>account_dim_key: 1001<br/>asset_value: 255000<br/>New row inserted"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M2["snap_dt: 2026-02-11<br/>ETF_31_60_DAYS: 2299<br/>Refreshed: 02:30<br/>FAST refresh: <5s"]
    end
    
    D2 -->|FK Link| F2
    F2 --> M2
    style D2 fill:#0277bd,color:#fff
    style F2 fill:#1b5e20,color:#fff
    style M2 fill:#2e7d32,color:#fff
```

#### T+2: After Intraday Update (14:30:05)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM (Type 2)"
        D3A["account_dim_key: 1001<br/>investment_type: ETF<br/>effective_to: 2026-02-11<br/>is_current: N<br/>Closed at 14:30"]
        D3B["account_dim_key: 1002<br/>investment_type: STOCK<br/>effective_from: 2026-02-11<br/>effective_to: 9999-12-31<br/>is_current: Y<br/>Created at 14:30"]
    end
    
    subgraph "ACCOUNT_FACT"
        F3["snap_dt: 2026-02-11<br/>account_number: A-0000123456<br/>account_dim_key: 1002<br/>Updated FK at 14:30"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M3["snap_dt: 2026-02-11<br/>ETF_31_60_DAYS: 2299<br/>STOCK_31_60_DAYS: 1800<br/>Last refresh: 14:25"]
    end
    
    D3A -.->|Old version| F3
    D3B -->|FK Link| F3
    F3 --> M3
    style D3A fill:#e64a19,color:#fff
    style D3B fill:#f57f17,color:#fff
    style F3 fill:#1b5e20,color:#fff
    style M3 fill:#b71c1c,color:#fff
```

#### T+3: After MV Refresh (14:30:08)

```mermaid
graph LR
    subgraph "ACCOUNT_DIM (Type 2)"
        D4A["account_dim_key: 1001<br/>investment_type: ETF<br/>is_current: N"]
        D4B["account_dim_key: 1002<br/>investment_type: STOCK<br/>is_current: Y"]
    end
    
    subgraph "ACCOUNT_FACT"
        F4["snap_dt: 2026-02-11<br/>account_number: A-0000123456<br/>account_dim_key: 1002"]
    end
    
    subgraph "MV_REBALANCE_SUMMARY"
        M4["snap_dt: 2026-02-11<br/>ETF_31_60_DAYS: 2298<br/>STOCK_31_60_DAYS: 1801<br/>Refreshed: 14:30<br/>FAST: 3 seconds"]
    end
    
    D4B -->|FK Link| F4
    F4 --> M4
    style D4A fill:#e64a19,color:#fff
    style D4B fill:#f57f17,color:#fff
    style F4 fill:#1b5e20,color:#fff
    style M4 fill:#2e7d32,color:#fff
```

---

## Side-by-Side Timeline Comparison {#timeline-comparison}

### Complete 24-Hour Cycle Comparison

```mermaid
gantt
    title Side-by-Side: 24-Hour Processing Comparison
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Design 1 Nightly
    Batch Start              :00:00, 1m
    Processing               :00:01, 4h34m
    MV COMPLETE Refresh      :02:30, 2h
    Batch Complete           :04:35, 1m
    
    section Design 2 Nightly
    Batch Start              :00:00, 1m
    Processing               :00:01, 2h34m
    MV FAST Refresh          :02:30, 5m
    Batch Complete           :02:35, 1m
    
    section Design 1 Intraday
    CDC Processing           :08:00, 12h
    MV Refresh #1 (15min)    :08:15, 2m
    MV Refresh #2 (30min)    :08:30, 2m
    MV Refresh Continues     :08:30, 11h30m
    
    section Design 2 Intraday
    CDC Processing           :08:00, 12h
    MV Refresh #1 (5min)     :08:05, 3s
    MV Refresh #2 (10min)     :08:10, 3s
    MV Refresh Continues     :08:10, 11h50m
```

---

### Operation Count Comparison

```mermaid
flowchart LR
    subgraph "Design 1: Per CDC Message"
        D1A[1. Check Event State]
        D1B[2. Update DIM]
        D1C[3. Update FACT]
        D1D[4. Calculate Deltas]
        D1E[5. Update Overlay]
        D1F[6. Update Event State]
        D1G[7. Update Offset]
        
        D1A --> D1B --> D1C --> D1D --> D1E --> D1F --> D1G
    end
    
    subgraph "Design 2: Per CDC Message"
        D2A[1. Close DIM Row]
        D2B[2. Insert DIM Row]
        D2C[3. Update FACT FK]
        D2D[4. Commit]
        
        D2A --> D2B --> D2C --> D2D
    end
    
    style D1A fill:#c62828,color:#fff
    style D1B fill:#c62828,color:#fff
    style D1C fill:#c62828,color:#fff
    style D1D fill:#c62828,color:#fff
    style D1E fill:#c62828,color:#fff
    style D1F fill:#c62828,color:#fff
    style D1G fill:#c62828,color:#fff
    
    style D2A fill:#2e7d32,color:#fff
    style D2B fill:#2e7d32,color:#fff
    style D2C fill:#2e7d32,color:#fff
    style D2D fill:#2e7d32,color:#fff
```

---

## Partition Exchange vs Full Merge: Nightly Update Comparison {#partition-exchange-comparison}

### Design 1: Full Merge Approach

```mermaid
flowchart LR
    subgraph "Input"
        STG["ACCOUNT_STG<br/>(10M rows)<br/>Staged data"]
    end
    
    subgraph "Merge Process"
        M["MERGE INTO ACCOUNT_DAY_FCT<br/>USING ACCOUNT_STG<br/>WHEN MATCHED THEN UPDATE<br/>WHEN NOT MATCHED THEN INSERT"]
        
        L["Operations per row:<br/>✓ Lookup existing<br/>✓ Compare values<br/>✓ Row-by-row log<br/>✓ UNDO/REDO tracking"]
    end
    
    subgraph "Duration & Cost"
        D1["Time: 30-45 minutes<br/>I/O: Heavy<br/>Logging: Extensive<br/>CPU: Medium-High<br/>Lock Duration: 45 min"]
    end
    
    subgraph "MV Refresh"
        R1["MV Reconstruction:<br/>Full table scan<br/>All 10M rows aggregated<br/>Duration: 1-2 minutes"]
    end
    
    STG --> M
    M --> L
    L --> D1
    D1 --> R1
    
    style M fill:#c62828,color:#fff
    style L fill:#c62828,color:#fff
    style D1 fill:#e64a19,color:#fff
    style R1 fill:#c62828,color:#fff
```

**Design 1 Characteristics:**
- **Row-by-row processing:** Each of 10M rows compared and updated individually
- **Full logging:** Every change logged for recoverability
- **MV Reconstruction:** Scans entire ACCOUNT_DAY_FCT and rebuilds from scratch
- **Impact:** Long nightly window (45 min), extended table locks

---

### Design 2: Partition Exchange Approach

```mermaid
flowchart LR
    subgraph "Input"
        STG["ACCOUNT_STG<br/>(10M rows)<br/>Staged data"]
    end
    
    subgraph "Exchange Process"
        PE["1. CREATE account_fact_exch<br/>2. SELECT + JOIN in temp table<br/>3. EXCHANGE PARTITION<br/>ALTER TABLE SWAP"]
        
        L["Operations:<br/>✓ Bulk insert (5M pairs)<br/>✓ Index build (temp)<br/>✓ Metadata swap<br/>✓ Minimal logging"]
    end
    
    subgraph "Duration & Cost"
        D2["Time: 2-3 minutes<br/>I/O: Light (organized loads)<br/>Logging: Minimal<br/>CPU: Low<br/>Lock Duration: Seconds"]
    end
    
    subgraph "MV Refresh"
        R2["MV Reconstruction:<br/>Read new partition only<br/>Log-based aggregation<br/>Duration: <5 seconds"]
    end
    
    STG --> PE
    PE --> L
    L --> D2
    D2 --> R2
    
    style PE fill:#0277bd,color:#fff
    style L fill:#0277bd,color:#fff
    style D2 fill:#2e7d32,color:#fff
    style R2 fill:#2e7d32,color:#fff
```

**Design 2 Characteristics:**
- **Bulk operations:** Data inserted in one organized statement
- **Minimal logging:** Partition exchange is near-instantaneous at metadata layer
- **MV Reconstruction:** Targets only new partition + MV logs for incremental rebuild
- **Impact:** Short nightly window (3 min), minimal locking

---

### MV Reconstruction Process Comparison

```mermaid
sequenceDiagram
    participant Fact as ACCOUNT_DAY_FCT
    participant MV as Materialized View
    participant Oracle as Oracle Engine
    
    rect rgb(198, 40, 40)
        Note over Fact,Oracle: Design 1: Full Reconstruction
        
        Oracle->>Fact: SELECT * FROM ACCOUNT_DAY_FCT<br/>snap_dt >= 2026-02-11
        Fact-->>MV: Stream all 10M+ rows
        Oracle->>MV: GROUP BY rebalance bucket<br/>GROUP BY qlh bucket<br/>Aggregate counts
        Note over Oracle: Full scan of fact table<br/>All aggregations rebuilt<br/>Duration: 1-2 minutes
    end
    
    rect rgb(46, 125, 50)
        Note over Fact,Oracle: Design 2: Incremental Reconstruction
        
        Oracle->>Fact: SELECT * FROM new partition<br/>ACCOUNT_FACT_20260211
        Fact-->>MV: Stream 5M rows (new data)
        Oracle->>MV: Apply dimension lookups<br/>GROUP BY aggregations<br/>Merge with existing MV
        Note over Oracle: Scan only new partition<br/>+ incremental joins<br/>Duration: <5 seconds
    end
```

---



### Design 1: Complete Data Flow with All Components

```mermaid
flowchart TB
    subgraph "Source Systems"
        IIDR[IIDR CDC Source]
        BulkFeed[Nightly Bulk Feed]
    end
    
    subgraph "Message Queue"
        Kafka[Kafka Topic<br/>Partitioned by account_id]
    end
    
    subgraph "Processing Layer"
        BatchConsumer[Spring Batch Consumer<br/>Micro-batches]
        NightlyProcessor[Nightly Batch Processor]
    end
    
    subgraph "Oracle Database - Design 1"
        subgraph "Dimension"
            Dim[ACCOUNT_DIM<br/>Type 1 SCD<br/>Current values only]
        end
        
        subgraph "FactTable"
            Fact1[ACCOUNT_DAY_FCT<br/>Daily snapshots<br/>+ snapshot columns]
        end
        
        subgraph "State Tracking"
            EventState[ACCOUNT_EVENT_STATE<br/>Idempotency tracking]
            CDCState[CDC_APPLY_STATE<br/>Kafka offsets]
        end
        
        subgraph "Real-Time Adjustments"
            Overlay[SUMMARY_HOT_OVERLAY<br/>Delta tracking]
        end
        
        subgraph "Pre-Aggregations"
            MV[Materialized Views<br/>mv_rebalance_summary<br/>mv_qlh_weekly<br/>Refresh: 15-30 min]
        end
    end
    
    subgraph "UI Layer"
        SummaryAPI[Summary Grid API]
        DetailAPI[Detail Grid API]
    end
    
    BulkFeed --> NightlyProcessor
    IIDR --> Kafka
    Kafka --> BatchConsumer
    
    NightlyProcessor --> Dim
    NightlyProcessor --> Fact1
    NightlyProcessor --> MV
    
    BatchConsumer --> EventState
    BatchConsumer --> Dim
    BatchConsumer --> Fact1
    BatchConsumer --> Overlay
    BatchConsumer --> EventState
    BatchConsumer --> CDCState
    
    MV --> SummaryAPI
    Overlay --> SummaryAPI
    Fact1 --> DetailAPI
    Dim --> DetailAPI
    
    style Overlay fill:#f57f17,color:#fff
    style EventState fill:#e64a19,color:#fff
    style CDCState fill:#e64a19,color:#fff
    style MV fill:#0277bd,color:#fff
```

---

### Design 2: Complete Data Flow with All Components

```mermaid
flowchart TB
    subgraph "Source Systems"
        IIDR[IIDR CDC Source]
        BulkFeed[Nightly Bulk Feed]
    end
    
    subgraph "Message Queue"
        Kafka[Kafka Topic<br/>Exactly-Once Semantics<br/>Transactional]
    end
    
    subgraph "Processing Layer"
        BatchConsumer[Spring Batch Consumer<br/>Transactional<br/>Single transaction per message]
        NightlyProcessor[Nightly Batch Processor]
    end
    
    subgraph "Oracle Database - Design 2"
        subgraph "Dimension"
            Dim[ACCOUNT_DIM<br/>Type 2 SCD<br/>Historical versions<br/>effective_from/to dates]
        end
        
        subgraph "FactTable"
            Fact2[ACCOUNT_FACT<br/>Daily snapshots<br/>FK to dimension<br/>Partition exchange]
        end
        
        subgraph "Services"
            Plan[SERVICE_PLAN<br/>DCA/TET enrollment]
            Run[SERVICE_RUN<br/>Execution events]
        end
        
        subgraph "Pre-Aggregations"
            MV[Materialized Views<br/>mv_rebalance_summary<br/>mv_qlh_weekly<br/>FAST refresh: 5 min]
        end
        
        subgraph "Temporary (Batch Only)"
            Staging[ACCOUNT_STG<br/>Temporary staging<br/>account_fact_exch<br/>Exchange table]
        end
    end
    
    subgraph "UI Layer"
        SummaryAPI[Summary Grid API]
        DetailAPI[Detail Grid API]
    end
    
    BulkFeed --> NightlyProcessor
    IIDR --> Kafka
    Kafka --> BatchConsumer
    
    NightlyProcessor --> Staging
    Staging --> Dim
    Staging --> Fact2
    NightlyProcessor --> MV
    
    BatchConsumer --> Dim
    BatchConsumer --> Fact2
    BatchConsumer --> Plan
    BatchConsumer --> Run
    
    MV --> SummaryAPI
    Fact2 --> DetailAPI
    Dim --> DetailAPI
    
    style Dim fill:#0277bd,color:#fff
    style Fact2 fill:#1b5e20,color:#fff
    style MV fill:#2e7d32,color:#fff
    style Kafka fill:#f57f17,color:#fff
```

---

### MV Refresh Comparison

```mermaid
sequenceDiagram
    participant Scheduler as MV Scheduler
    participant MV1 as Design 1 MV
    participant Fact1 as ACCOUNT_DAY_FCT
    participant Overlay1 as SUMMARY_HOT_OVERLAY
    participant MV2 as Design 2 MV
    participant Fact2 as ACCOUNT_FACT
    participant Dim2 as ACCOUNT_DIM
    
    Note over Scheduler,Dim2: MV Refresh Cycle Comparison
    
    rect rgb(198, 40, 40)
        Note over Scheduler,Overlay1: Design 1: COMPLETE Refresh (15-30 min interval)
        Scheduler->>MV1: REFRESH COMPLETE
        MV1->>Fact1: Scan entire partition<br/>Rebuild all aggregations
        Fact1-->>MV1: Return all data
        MV1->>MV1: Recalculate counts<br/>Duration: 1-2 minutes
        MV1->>Overlay1: TRUNCATE overlay<br/>Clear deltas
        Overlay1-->>MV1: Confirmed
        MV1-->>Scheduler: Refresh Complete
    end
    
    rect rgb(46, 125, 50)
        Note over Scheduler,Dim2: Design 2: FAST Refresh (5 min interval)
        Scheduler->>MV2: REFRESH FAST
        MV2->>MV2: Check MV Logs<br/>Incremental changes only
        MV2->>Fact2: Apply delta changes<br/>From MV logs
        MV2->>Dim2: Join for dimension values<br/>If needed
        MV2-->>Scheduler: Refresh Complete<br/>Duration: <5 seconds
    end
```

---

### UI Query Flow Comparison

```mermaid
sequenceDiagram
    participant User as User
    participant UI as React UI
    participant API as Spring Boot API
    participant DB1 as Design 1 Database
    participant DB2 as Design 2 Database
    
    User->>UI: Request Summary Grid<br/>"Show rebalance buckets"
    
    rect rgb(198, 40, 40)
        Note over UI,DB1: Design 1 Query Flow
        UI->>API: GET /api/summary/rebalance
        API->>DB1: Query MV_REBALANCE_SUMMARY<br/>WHERE snap_dt = today
        DB1-->>API: Return MV results
        API->>DB1: Query SUMMARY_HOT_OVERLAY<br/>WHERE snap_dt = today
        DB1-->>API: Return overlay deltas
        API->>API: Combine MV + Overlay<br/>Apply deltas to counts
        API-->>UI: Return combined results
        UI-->>User: Display summary grid
    end
    
    rect rgb(46, 125, 50)
        Note over UI,DB2: Design 2 Query Flow
        UI->>API: GET /api/summary/rebalance
        API->>DB2: Query MV_REBALANCE_SUMMARY<br/>WHERE snap_dt = today
        DB2-->>API: Return MV results<br/>(Already current, refreshed 5 min ago)
        API-->>UI: Return results
        UI-->>User: Display summary grid
    end
```

---

### Data Freshness Timeline

```mermaid
gantt
    title Data Freshness Comparison Over 1 Hour
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Design 1 Freshness
    MV Refresh #1 (15min)      :08:15, 2m
    Stale Period #1            :08:17, 13m
    MV Refresh #2 (30min)      :08:30, 2m
    Stale Period #2            :08:32, 13m
    MV Refresh #3 (45min)      :08:45, 2m
    Stale Period #3            :08:47, 13m
    MV Refresh #4 (60min)      :09:00, 2m
    
    section Design 2 Freshness
    MV Refresh #1 (5min)       :08:05, 3s
    Stale Period #1            :08:05, 4m57s
    MV Refresh #2 (10min)      :08:10, 3s
    Stale Period #2            :08:10, 4m57s
    MV Refresh #3 (15min)      :08:15, 3s
    Stale Period #3            :08:15, 4m57s
    MV Refresh #4 (20min)      :08:20, 3s
    Stale Period #4            :08:20, 4m57s
    MV Refresh #5 (25min)      :08:25, 3s
    Stale Period #5            :08:25, 4m57s
    MV Refresh #6 (30min)      :08:30, 3s
```

---

## Key Metrics Summary

### Processing Metrics

| Metric | Design 1 | Design 2 |
|--------|----------|-----------|
| **Nightly Batch Duration** | ~4.5 hours | ~2.5 hours |
| **MV Refresh Duration** | 1-2 minutes (COMPLETE) | <5 seconds (FAST) |
| **MV Refresh Frequency** | Every 15-30 minutes | Every 5 minutes |
| **Operations per CDC Message** | 7 operations | 1 transaction (3 SQL statements) |
| **Data Freshness (Max Staleness)** | 15-30 minutes | 5 minutes |
| **Permanent Tables** | 11+ tables | 6 tables |
| **Staging Tables (Temporary)** | ACCOUNT_STG | ACCOUNT_STG + account_fact_exch |
| **Overlay Table Required** | Yes | No |
| **Idempotency Management** | Manual (2 tables) | Framework (Kafka) |
| **Nightly Batch Method** | MERGE operations | Partition exchange (instant) |

### Timeline Summary

**Design 1:**
- Nightly batch: 23:00 - 04:35 (4h 35m)
- MV refresh: Every 15-30 minutes, takes 1-2 minutes
- Data can be stale up to 30 minutes

**Design 2:**
- Nightly batch: 23:00 - 02:35 (2h 35m)
- MV refresh: Every 5 minutes, takes <5 seconds
- Data can be stale up to 5 minutes

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-16  
**Author:** Technical Analysis Team
