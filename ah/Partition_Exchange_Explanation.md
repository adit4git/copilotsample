# Partition Exchange: Explained Simply

## What is Partition Exchange?

**Partition Exchange** is an Oracle database feature that allows you to **instantly swap** a partition (a section of a large table) with a standalone table. It's like swapping two boxes - you don't move the contents, you just change which box is labeled as what.

---

## Why Do We Need It?

### The Problem: Loading Millions of Rows

Imagine you have a table with **10 million accounts**, and every night you need to update today's data for all accounts.

**Traditional Approach (MERGE/INSERT/UPDATE):**
```
For each of 10 million accounts:
  1. Check if row exists
  2. If exists, UPDATE it
  3. If not, INSERT it
  4. Update indexes
  5. Write to transaction log
```

**Problems:**
- Takes **hours** to complete
- Locks the table during updates
- Generates massive transaction logs
- Can cause performance issues for queries running at the same time

---

## How Partition Exchange Works

### Step-by-Step Process

#### Step 1: Build the New Data Separately

Instead of updating the main table directly, you:
1. Load new data into a **staging table** (`ACCOUNT_STG`)
2. Transform and validate the data
3. Create a **temporary exchange table** (`account_fact_exch`) with the final data

```
Staging Table (ACCOUNT_STG)
├── Account 1: $250,000
├── Account 2: $120,000
├── Account 3: $500,000
└── ... (10 million accounts)

↓ Transform & Validate ↓

Exchange Table (account_fact_exch)
├── Account 1: $255,000 (updated)
├── Account 2: $122,000 (updated)
├── Account 3: $505,000 (updated)
└── ... (10 million accounts, ready to go)
```

#### Step 2: Swap Instantly

Once the exchange table is ready, you swap it with the partition:

```sql
ALTER TABLE account_fact
  EXCHANGE PARTITION FOR (TRUNC(SYSDATE))  -- Today's partition
  WITH TABLE account_fact_exch             -- The new data
  INCLUDING INDEXES                        -- Swap indexes too
  WITHOUT VALIDATION;                      -- Skip validation (we already did it)
```

**What happens:**
- Oracle **instantly** swaps the metadata (pointers)
- No data is physically moved
- The old partition becomes the exchange table
- The exchange table becomes the partition
- Takes **seconds** instead of hours!

---

## Visual Example

### Before Exchange

```
Main Table: ACCOUNT_FACT
├── Partition: 2026-02-10 (yesterday)
│   ├── Account 1: $250,000
│   ├── Account 2: $120,000
│   └── ...
│
├── Partition: 2026-02-11 (today) ← We want to replace this
│   ├── Account 1: $250,000 (old)
│   ├── Account 2: $120,000 (old)
│   └── ...
│
└── Partition: 2026-02-12 (future)
    └── (empty)

Exchange Table: account_fact_exch
├── Account 1: $255,000 (new)
├── Account 2: $122,000 (new)
└── ... (ready to swap)
```

### After Exchange

```
Main Table: ACCOUNT_FACT
├── Partition: 2026-02-10 (yesterday)
│   ├── Account 1: $250,000
│   ├── Account 2: $120,000
│   └── ...
│
├── Partition: 2026-02-11 (today) ← Now has new data!
│   ├── Account 1: $255,000 (new)
│   ├── Account 2: $122,000 (new)
│   └── ...
│
└── Partition: 2026-02-12 (future)
    └── (empty)

Old Exchange Table: account_fact_exch
├── Account 1: $250,000 (old data, will be dropped)
├── Account 2: $120,000 (old data, will be dropped)
└── ...
```

---

## Real-World Analogy

Think of it like this:

**Traditional Approach (MERGE):**
- Like renovating a room while people are still using it
- You have to move furniture piece by piece
- Takes a long time
- Disrupts everyone

**Partition Exchange:**
- Like having a completely renovated room ready next door
- When ready, you just swap the room numbers
- Instant!
- No disruption

---

## Benefits

### 1. **Speed**
- **Traditional MERGE:** 2-4 hours for 10 million rows
- **Partition Exchange:** 2-5 minutes (mostly for building the exchange table)

### 2. **Minimal Locking**
- The main table is only locked for **seconds** during the swap
- Queries can continue on other partitions

### 3. **Reduced Transaction Logs**
- No UPDATE statements = less logging
- Better for database performance

### 4. **Atomic Operation**
- Either the swap succeeds completely, or it fails completely
- No partial updates

### 5. **Easy Rollback**
- If something goes wrong, the old partition is still in the exchange table
- Can swap back if needed

---

## Example: Nightly Batch Process

### Timeline Comparison

**Design 1 (MERGE approach):**
```
23:00 - Start batch
23:30 - Load staging (30 min)
00:00 - Validate data (30 min)
00:30 - MERGE into fact table (2 hours) ← SLOW!
02:30 - Refresh MVs (1-2 min)
02:35 - Complete
```

**Design 2 (Partition Exchange):**
```
23:00 - Start batch
23:30 - Load staging (30 min)
00:00 - Validate data (30 min)
00:30 - Build exchange table (30 min)
01:00 - Exchange partition (5 seconds) ← INSTANT!
01:00 - Refresh MVs (5 seconds)
01:01 - Complete
```

**Time Saved:** ~1.5 hours per night!

---

## Code Example

### Traditional MERGE Approach

```sql
-- This takes HOURS for 10 million rows
MERGE INTO account_fact f
USING account_stg s
ON (f.snap_dt = TRUNC(SYSDATE) AND f.account_number = s.account_number)
WHEN MATCHED THEN
  UPDATE SET 
    asset_value = s.asset_value,
    rebalance_dt = s.rebalance_dt,
    -- ... many more columns
WHEN NOT MATCHED THEN
  INSERT (snap_dt, account_number, asset_value, ...)
  VALUES (TRUNC(SYSDATE), s.account_number, s.asset_value, ...);
```

**Problems:**
- Processes row by row
- Updates indexes for each row
- Generates massive transaction logs
- Locks table for hours

### Partition Exchange Approach

```sql
-- Step 1: Build exchange table (can take time, but doesn't lock main table)
CREATE TABLE account_fact_exch AS
SELECT 
  TRUNC(SYSDATE) AS snap_dt,
  s.account_number,
  d.account_dim_key,
  s.asset_value,
  s.rebalance_dt,
  calc_qlh_next_run(s.qlh_enrollment_dt, TRUNC(SYSDATE)) AS qlh_next_run_dt
FROM account_stg s
JOIN account_dim d ON d.account_number = s.account_number
                  AND d.is_current = 'Y';

-- Step 2: Add constraints (for data integrity)
ALTER TABLE account_fact_exch
  ADD CONSTRAINT exch_pk PRIMARY KEY (snap_dt, account_number);

-- Step 3: Swap instantly! (takes seconds)
ALTER TABLE account_fact
  EXCHANGE PARTITION FOR (TRUNC(SYSDATE))
  WITH TABLE account_fact_exch
  INCLUDING INDEXES
  WITHOUT VALIDATION;

-- Step 4: Cleanup
DROP TABLE account_fact_exch;  -- Old data, no longer needed
```

**Benefits:**
- Builds new data separately (no locking)
- Swaps instantly (seconds)
- Minimal transaction logs
- No disruption to queries

---

## Requirements for Partition Exchange

### 1. **Table Must Be Partitioned**
The main table must use Oracle partitioning:
```sql
CREATE TABLE account_fact (
  snap_dt DATE,
  account_number VARCHAR2(50),
  ...
)
PARTITION BY RANGE (snap_dt) INTERVAL (NUMTOYMINTERVAL(1, 'MONTH'))
(
  PARTITION p_initial VALUES LESS THAN (DATE '2024-01-01')
);
```

### 2. **Exchange Table Must Match Structure**
- Same columns
- Same data types
- Same constraints (or compatible ones)

### 3. **Partition Key Must Match**
The exchange table's partition key column must have values that match the partition being exchanged.

---

## When to Use Partition Exchange

### ✅ Good Use Cases:
- **Nightly batch loads** (like our scenario)
- **Large data updates** (millions of rows)
- **Time-sensitive operations** (need to minimize downtime)
- **Partitioned tables** with date-based partitions

### ❌ Not Suitable For:
- **Small updates** (few hundred rows - MERGE is fine)
- **Non-partitioned tables** (can't use partition exchange)
- **Frequent intraday updates** (use MERGE for individual rows)

---

## In Our Design Context

### Design 1 (Main v5)
- Uses **MERGE** operations
- Updates rows one by one
- Takes longer but simpler to understand

### Design 2 (Gilfoyle Revised)
- Uses **Partition Exchange** for nightly batch
- Builds new partition separately
- Swaps instantly
- Much faster for large volumes

---

## What is MV FAST Refresh?

**MV** = **Materialized View** (a pre-computed, stored result of a query, like a cached summary table)  
**FAST refresh** = updating that stored result by applying only the **changes** since the last refresh, instead of recalculating everything.

### The Problem: Summary Queries Are Slow

The UI needs answers like:
- "How many accounts need rebalancing in the next 30 days?"
- "How many QLH accounts per week?"

Running these **aggregations** (COUNT, SUM, GROUP BY) on 10 million rows every time someone opens the summary screen would be **slow** (seconds to minutes).

**Solution:** Store the pre-computed answers in a **Materialized View (MV)**. The UI then reads from the MV (fast), and we periodically **refresh** the MV so it stays up to date.

### Two Ways to Refresh an MV

| Method | What It Does | Time | When Used |
|--------|----------------|------|-----------|
| **COMPLETE refresh** | Rebuilds the entire MV from scratch (full scan of base tables) | 1–2 minutes | Nightly after bulk load |
| **FAST refresh** | Applies only the **changes** since last refresh (uses MV logs) | **&lt;5 seconds** | Intraday, every 5–15 min |

### How FAST Refresh Works

1. **MV Log (Materialized View Log)**  
   Oracle keeps a small **log table** on the base table(s) that records which rows were **inserted, updated, or deleted** since the last refresh.

2. **On refresh**  
   Instead of scanning all 10M rows again, Oracle:
   - Reads only the **log** (recent changes)
   - Applies those changes to the existing MV rows (add/update/delete)
   - Result: MV is updated in **seconds**, not minutes

**Analogy:**
- **COMPLETE refresh:** Re-count every book in the library.
- **FAST refresh:** Only count the books that were added or removed since last count.

### Why It Matters in Our Designs

- **Design 1 (Main v5):** Uses **COMPLETE** refresh every 15–30 minutes (1–2 min each time). To hide staleness, it adds a **SUMMARY_HOT_OVERLAY** table with deltas between refreshes.
- **Design 2 (Gilfoyle):** Uses **FAST** refresh every 5 minutes (&lt;5 sec). The MV is fresh often enough that **no overlay table** is needed.

### Summary

**MV FAST refresh** = Update the materialized view by applying only **incremental changes** (via MV logs), so the summary stays up to date in **seconds** instead of minutes, and you can refresh frequently (e.g. every 5 minutes) without an overlay table.

---

## Summary

**Partition Exchange** is like:
- 🏠 Swapping houses instead of moving furniture
- 📦 Swapping boxes instead of repacking them
- 🔄 Swapping room numbers instead of renovating

**Key Takeaway:**
Instead of updating millions of rows one by one (slow), you build a complete new partition separately, then swap it instantly (fast). This is why Design 2's nightly batch completes in ~2.5 hours instead of ~4.5 hours!

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-16
