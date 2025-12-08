package com.example.batchmultidb.datasource;

import org.springframework.jdbc.core.JdbcTemplate;

public class DefaultConnectionFactory implements ConnectionFactory {

    private final JdbcTemplate oracleJdbcTemplate;
    private final JdbcTemplate h2JdbcTemplate;

    public DefaultConnectionFactory(JdbcTemplate oracleJdbcTemplate,
                                    JdbcTemplate h2JdbcTemplate) {
        this.oracleJdbcTemplate = oracleJdbcTemplate;
        this.h2JdbcTemplate = h2JdbcTemplate;
    }

    @Override
    public JdbcTemplate getJdbcTemplate(DataStoreType storeType) {
        return switch (storeType) {
            case ORACLE -> oracleJdbcTemplate;
            case H2 -> h2JdbcTemplate;
        };
    }
}
