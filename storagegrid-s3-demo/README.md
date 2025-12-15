# StorageGRID S3 Demo (Spring Boot)

A minimal Spring Boot microservice with:
- `POST /api/files/upload` to upload a multipart file to an S3 bucket
- `GET  /api/files` to list objects from the bucket

This is designed to work with **S3-compatible endpoints** such as **NetApp StorageGRID**.

## Prereqs
- Java 17+
- Maven 3.9+

## Configure
Edit `src/main/resources/application.yml`:

- `s3.endpoint` = **base endpoint** (no bucket), e.g. `https://s3.company.com:10443`
- `s3.bucket` = bucket name
- `s3.accessKey`, `s3.secretKey` = tenant access keys
- `s3.pathStyle` = `true` is often necessary for StorageGRID unless endpoint domain names are configured

> If you can upload but cannot list, double-check:
> - you're not accidentally using virtual-hosted style without StorageGRID endpoint domain names/DNS/cert
> - the user policy includes `s3:ListBucket` on the bucket ARN

## Run
```bash
mvn spring-boot:run
```

## Test

### Upload
```bash
curl -F "file=@./hello.txt" "http://localhost:8080/api/files/upload?prefix=demo/"
```

### List
```bash
curl "http://localhost:8080/api/files?prefix=demo/&maxKeys=100"
```

## Notes for StorageGRID
- If your grid is configured for virtual-hosted style (endpoint domain names + DNS + cert), you *may* set `pathStyle: false`.
- If you see failures that look like "NoSuchKey"/404 on list, it’s often endpoint style mismatch or missing ListBucket permission.
