package com.example.batchmultidb.datasource;

import org.springframework.jdbc.core.JdbcTemplate;

public interface ConnectionFactory {
    JdbcTemplate getJdbcTemplate(DataStoreType storeType);
}
