package com.example.batchmultidb.batch;

import com.example.batchmultidb.domain.Customer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.ExecutionContext;
import org.springframework.batch.item.ItemStreamException;
import org.springframework.batch.item.ItemStreamReader;
import org.springframework.core.io.Resource;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;

@Slf4j
public class LocalCsvCustomerItemReader implements ItemStreamReader<Customer> {

    private final Resource resource;
    private BufferedReader reader;
    private Iterator<String> lineIterator;
    private boolean headerSkipped = false;

    public LocalCsvCustomerItemReader(Resource resource) {
        this.resource = resource;
    }

    @Override
    public Customer read() {
        if (lineIterator == null || !lineIterator.hasNext()) {
            return null;
        }

        String line = lineIterator.next();
        
        // skip header if present
        if (!headerSkipped && line.toLowerCase().startsWith("firstname")) {
            headerSkipped = true;
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
            this.reader = new BufferedReader(
                    new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8)
            );
            this.lineIterator = reader.lines().iterator();
            this.headerSkipped = false;
            log.info("Opened local CSV file: {}", resource.getFilename());
        } catch (IOException e) {
            throw new ItemStreamException("Failed to open local CSV file", e);
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
                log.info("Closed local CSV file reader");
            }
        } catch (IOException e) {
            log.error("Error closing reader", e);
        }
    }
}
