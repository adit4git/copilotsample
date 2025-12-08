package com.example.batchmultidb.batch;

import com.example.batchmultidb.domain.Customer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;
import org.springframework.data.jpa.repository.JpaRepository;

@Slf4j
@RequiredArgsConstructor
public class LocalDbCustomerItemWriter implements ItemWriter<Customer> {

    private final JpaRepository<Customer, Long> repository;

    @Override
    public void write(Chunk<? extends Customer> chunk) throws Exception {
        if (chunk == null || chunk.isEmpty()) {
            return;
        }

        repository.saveAll(chunk);
        log.info("Wrote {} customers to H2 database", chunk.size());
    }
}
