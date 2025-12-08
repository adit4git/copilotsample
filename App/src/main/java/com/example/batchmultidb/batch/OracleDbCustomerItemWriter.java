package com.example.batchmultidb.batch;

import com.example.batchmultidb.domain.Customer;
import com.example.batchmultidb.repository.oracle.CustomerOracleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;

@Slf4j
@RequiredArgsConstructor
public class OracleDbCustomerItemWriter implements ItemWriter<Customer> {

    private final CustomerOracleRepository repository;

    @Override
    public void write(Chunk<? extends Customer> chunk) {
        if (chunk == null || chunk.isEmpty()) {
            return;
        }

        repository.saveAll(chunk);
        log.info("Wrote {} customers to Oracle database", chunk.size());
    }
}
