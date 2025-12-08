package com.example.batchmultidb.batch;

import com.example.batchmultidb.datasource.ConnectionFactory;
import com.example.batchmultidb.datasource.DataStoreType;
import com.example.batchmultidb.domain.Customer;
import com.example.batchmultidb.repository.oracle.CustomerOracleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;

@Slf4j
@RequiredArgsConstructor
public class MultiDbCustomerItemWriter implements ItemWriter<Customer> {

    private final CustomerOracleRepository oracleRepository;
    private final ConnectionFactory connectionFactory;

    @Override
    public void write(Chunk<? extends Customer> chunk) throws Exception {
        if (chunk == null || chunk.isEmpty()) {
            return;
        }

        List<? extends Customer> items = chunk.getItems();
        
        // 1) Save to Oracle through JPA
        oracleRepository.saveAll(items);

        // 2) Save to H2 through JDBC (audit table)
        JdbcTemplate h2 = connectionFactory.getJdbcTemplate(DataStoreType.H2);

        h2.batchUpdate(
                "INSERT INTO CUSTOMER_AUDIT (FIRST_NAME, LAST_NAME, EMAIL) VALUES (?, ?, ?)",
                items,
                items.size(),
                (ps, customer) -> {
                    ps.setString(1, customer.getFirstName());
                    ps.setString(2, customer.getLastName());
                    ps.setString(3, customer.getEmail());
                }
        );
        log.info("Wrote {} customers to Oracle and {} to H2 audit", items.size(), items.size());
    }
}
