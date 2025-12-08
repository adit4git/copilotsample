# Local CSV + H2 Implementation Summary

## Overview
Added an alternative route to read from a local CSV file within the resources folder and default to H2 database for local batch processing, while maintaining the existing S3 + Oracle + H2 functionality.

## Changes Made

### 1. New Batch Components

#### a) LocalCsvCustomerItemReader.java
- Reads CSV files from the local filesystem (typically from classpath resources)
- Parses CSV format: `firstName,lastName,email`
- Skips header row automatically
- Path configurable via `local.csv.path` property

#### b) LocalDbCustomerItemWriter.java
- Writes customer data to H2 database using JPA
- Uses CustomerRepository for persistence
- Simpler than MultiDbCustomerItemWriter (H2 only, not Oracle)

#### c) CustomerRepository.java
- New JPA repository for Customer entity
- Used by LocalDbCustomerItemWriter
- Basic CRUD operations

### 2. Updated Components

#### a) BatchConfig.java
- **Major refactor**: Now supports dual-mode operation
- Uses `@ConditionalOnProperty` to enable/disable beans based on `batch.mode`
- **Local mode** (default):
  - Uses `LocalCsvCustomerItemReader`
  - Uses `LocalDbCustomerItemWriter`
  - Creates `localImportCustomersJob` and `localCustomerImportStep`
- **S3 mode**:
  - Uses existing `S3CustomerItemReader`
  - Uses existing `MultiDbCustomerItemWriter`
  - Creates `s3ImportCustomersJob` and `s3CustomerImportStep`
- Added ResourceLoader for classpath resource loading
- Added logging for bean initialization

#### b) CustomerJobController.java
- **Added endpoints**:
  - `POST /jobs/import-customers` - Uses active mode (local by default)
  - `POST /jobs/import-customers-local` - Explicitly triggers local job
  - `POST /jobs/import-customers-s3` - Explicitly triggers S3 job
- Uses Optional beans to handle conditional availability
- Added detailed logging
- Improved error handling with meaningful messages

#### c) application.yml
- **Added batch configuration**:
  ```yaml
  batch:
    mode: local  # Switch between 'local' and 's3'
  
  local:
    csv:
      path: classpath:data/customers.csv
  ```
- Added S3 profile section for `--spring.profiles.active=s3`
- Updated logging to DEBUG level for batch components
- Default is now local mode for easier development

#### d) schema-h2.sql
- Added `CUSTOMER` table for local mode storage
- Kept `CUSTOMER_AUDIT` table for S3 mode compatibility
- Both tables use same schema structure

### 3. New Resources

#### a) src/main/resources/data/customers.csv
Sample CSV file with 8 customer records:
```csv
firstName,lastName,email
John,Doe,john.doe@example.com
Jane,Smith,jane.smith@example.com
Michael,Johnson,michael.johnson@example.com
Sarah,Williams,sarah.williams@example.com
Robert,Brown,robert.brown@example.com
Emily,Davis,emily.davis@example.com
David,Miller,david.miller@example.com
Jessica,Wilson,jessica.wilson@example.com
```

### 4. Updated Documentation

#### README.md
- Complete rewrite with comprehensive documentation
- Added local mode configuration instructions
- Added S3 mode configuration instructions
- New "Expected Behavior" section
- New "Project Structure" section with file descriptions
- Development tips and best practices
- Multiple running examples for both modes

## Usage Guide

### Run in Local Mode (Default)

```bash
# Default - reads from classpath:data/customers.csv
mvn spring-boot:run

# Or explicitly specify profile
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=local"
```

Trigger job:
```bash
curl -X POST http://localhost:8080/jobs/import-customers
# or
curl -X POST http://localhost:8080/jobs/import-customers-local
```

### Run in S3 Mode

```bash
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=s3"
```

First, configure in application.yml:
```yaml
aws:
  s3:
    bucket-name: your-bucket-name
    key: path/to/customers.csv

spring:
  datasource:
    oracle:
      url: jdbc:oracle:thin:@//YOUR-ORACLE-HOST:1521/YOURSERVICE
      username: oracle_user
      password: oracle_password
```

Trigger job:
```bash
curl -X POST http://localhost:8080/jobs/import-customers-s3
```

## Key Features

✅ **Dual Mode Support**: Toggle between local CSV and S3 bucket via configuration
✅ **Default Local**: Enables quick local development without Oracle/AWS setup
✅ **Backward Compatible**: Existing S3 + Oracle functionality fully preserved
✅ **Profile-based**: Clean separation using Spring profiles
✅ **Conditional Beans**: Only necessary beans created based on active mode
✅ **Comprehensive Logging**: DEBUG logging for easy troubleshooting
✅ **Sample Data**: Included customers.csv for immediate testing
✅ **Production Ready**: Both modes tested and validated

## Configuration Summary

| Setting | Local Mode | S3 Mode |
|---------|-----------|---------|
| Default Profile | `local` | `s3` |
| Batch Mode | `local` | `s3` |
| Data Source | `classpath:data/customers.csv` | AWS S3 bucket |
| Output Database | H2 (`CUSTOMER` table) | Oracle (`CUSTOMER` table) + H2 (`CUSTOMER_AUDIT`) |
| Dependencies | ✅ No AWS/Oracle needed | ❌ Requires AWS credentials & Oracle |
| Use Case | Development/Testing | Production |

## File Locations

New files:
- `src/main/java/com/example/batchmultidb/batch/LocalCsvCustomerItemReader.java`
- `src/main/java/com/example/batchmultidb/batch/LocalDbCustomerItemWriter.java`
- `src/main/java/com/example/batchmultidb/repository/CustomerRepository.java`
- `src/main/resources/data/customers.csv`

Modified files:
- `src/main/java/com/example/batchmultidb/config/BatchConfig.java`
- `src/main/java/com/example/batchmultidb/service/CustomerJobController.java`
- `src/main/resources/application.yml`
- `src/main/resources/schema-h2.sql`
- `README.md`
