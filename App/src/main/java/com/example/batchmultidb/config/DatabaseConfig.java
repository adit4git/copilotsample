package com.example.batchmultidb.config;

import com.example.batchmultidb.datasource.ConnectionFactory;
import com.example.batchmultidb.datasource.DefaultConnectionFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.core.JdbcTemplate;

import javax.sql.DataSource;

@Configuration
public class DatabaseConfig {

    // -------- DataSource properties ----------

    @Bean
    @ConfigurationProperties("spring.datasource.h2")
    public DataSourceProperties h2DataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    @ConfigurationProperties("spring.datasource.oracle")
    public DataSourceProperties oracleDataSourceProperties() {
        return new DataSourceProperties();
    }

    // -------- Primary DataSource switches between H2 (local) and Oracle (oracle/s3) ----------

    @Primary
    @Bean(name = "dataSource")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "local", matchIfMissing = true)
    public DataSource h2PrimaryDataSource() {
        return h2DataSourceProperties().initializeDataSourceBuilder().build();
    }

    @Primary
    @Bean(name = "dataSource")
    @ConditionalOnExpression("'${batch.mode:local}'!='local'")
    public DataSource oraclePrimaryDataSource() {
        return oracleDataSourceProperties().initializeDataSourceBuilder().build();
    }

    // -------- Secondary H2 DataSource for audit (oracle/s3 modes) ----------

    @Bean(name = "h2AuditDataSource")
    @ConditionalOnExpression("'${batch.mode:local}'!='local'")
    public DataSource h2AuditDataSource() {
        return h2DataSourceProperties().initializeDataSourceBuilder().build();
    }

    // -------- JdbcTemplates ----------

    @Bean
    @Qualifier("h2JdbcTemplate")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "local", matchIfMissing = true)
    public JdbcTemplate h2JdbcTemplateLocal(@Qualifier("dataSource") DataSource ds) {
        return new JdbcTemplate(ds);
    }

    @Bean
    @Qualifier("h2JdbcTemplate")
    @ConditionalOnExpression("'${batch.mode:local}'!='local'")
    public JdbcTemplate h2JdbcTemplateAudit(@Qualifier("h2AuditDataSource") DataSource ds) {
        return new JdbcTemplate(ds);
    }

    @Bean
    @Qualifier("oracleJdbcTemplate")
    @ConditionalOnExpression("'${batch.mode:local}'!='local'")
    public JdbcTemplate oracleJdbcTemplate(@Qualifier("dataSource") DataSource ds) {
        return new JdbcTemplate(ds);
    }

    // -------- ConnectionFactory implementation (S3 mode requires both stores) ----------

    @Bean
    @ConditionalOnProperty(name = "batch.mode", havingValue = "s3")
    public ConnectionFactory connectionFactory(
            @Qualifier("oracleJdbcTemplate") JdbcTemplate oracleJdbcTemplate,
            @Qualifier("h2JdbcTemplate") JdbcTemplate h2JdbcTemplate) {
        return new DefaultConnectionFactory(oracleJdbcTemplate, h2JdbcTemplate);
    }
}
