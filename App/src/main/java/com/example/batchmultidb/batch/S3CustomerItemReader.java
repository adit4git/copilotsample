package com.example.batchmultidb.batch;

import com.example.batchmultidb.domain.Customer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.ExecutionContext;
import org.springframework.batch.item.ItemStreamException;
import org.springframework.batch.item.ItemStreamReader;

import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;

@Slf4j
public class S3CustomerItemReader implements ItemStreamReader<Customer> {

    private final S3Client s3Client;
    private final String bucketName;
    private final String key;

    private BufferedReader reader;
    private Iterator<String> lineIterator;

    public S3CustomerItemReader(S3Client s3Client, String bucketName, String key) {
        this.s3Client = s3Client;
        this.bucketName = bucketName;
        this.key = key;
    }

    @Override
    public Customer read() {
        if (lineIterator == null || !lineIterator.hasNext()) {
            return null;
        }

        String line = lineIterator.next();
        // skip header if present
        if (line.toLowerCase().startsWith("firstName".toLowerCase())) {
            return read();
        }

        String[] parts = line.split(",");
        if (parts.length < 3) {
            log.warn("Skipping invalid line: {}", line);
            return read();
        }

        return Customer.builder()
                .firstName(parts[0].trim())
                .lastName(parts[1].trim())
                .email(parts[2].trim())
                .build();
    }

    @Override
    public void open(ExecutionContext executionContext) throws ItemStreamException {
        try {
            GetObjectRequest getObjectRequest = GetObjectRequest.builder()
                    .bucket(bucketName)
                    .key(key)
                    .build();

            InputStream is = s3Client.getObject(getObjectRequest);
            this.reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
            this.lineIterator = reader.lines().iterator();
        } catch (Exception e) {
            throw new ItemStreamException("Failed to open S3 object", e);
        }
    }

    @Override
    public void update(ExecutionContext executionContext) throws ItemStreamException {
        // no-op
    }

    @Override
    public void close() throws ItemStreamException {
        try {
            if (reader != null) {
                reader.close();
            }
        } catch (IOException e) {
            log.error("Error closing reader", e);
        }
    }
}
