package com.example.storagegrid.service;

import com.example.storagegrid.config.S3Properties;
import com.example.storagegrid.dto.FileInfo;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Request;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Response;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.time.Instant;
import java.util.List;

@Service
public class S3StorageService {

    private final S3Client s3;
    private final String bucket;

    public S3StorageService(S3Client s3, S3Properties props) {
        this.s3 = s3;
        this.bucket = props.bucket();
    }

    public FileInfo upload(String key, byte[] bytes, String contentType) {
        PutObjectRequest req = PutObjectRequest.builder()
                .bucket(bucket)
                .key(key)
                .contentType(contentType)
                .build();

        s3.putObject(req, RequestBody.fromBytes(bytes));
        return new FileInfo(key, bytes.length, Instant.now());
    }

    public List<FileInfo> list(String prefix, Integer maxKeys) {
        ListObjectsV2Request.Builder b = ListObjectsV2Request.builder()
                .bucket(bucket);

        if (prefix != null && !prefix.isBlank()) {
            b.prefix(prefix);
        }
        if (maxKeys != null && maxKeys > 0) {
            b.maxKeys(maxKeys);
        }

        ListObjectsV2Response resp = s3.listObjectsV2(b.build());

        if (resp.contents() == null) {
            return List.of();
        }

        return resp.contents().stream()
                .map(o -> new FileInfo(o.key(), o.size(), o.lastModified()))
                .toList();
    }
}
