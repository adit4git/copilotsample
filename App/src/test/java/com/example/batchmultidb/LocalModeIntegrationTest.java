package com.example.batchmultidb;

import com.example.batchmultidb.domain.Customer;
import com.example.batchmultidb.repository.CustomerRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import org.springframework.batch.core.ExitStatus;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

import javax.sql.DataSource;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("local")
@TestPropertySource(properties = {
        "batch.mode=local",
        "spring.main.web-application-type=none",
        "spring.batch.job.enabled=false",
        "spring.batch.jdbc.initialize-schema=always"
})
class LocalModeIntegrationTest {

    @Autowired
    private JobLauncher jobLauncher;

    @Autowired
    @Qualifier("localImportCustomersJob")
    private Job localJob;

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private DataSource dataSource;

    @BeforeEach
    void initializeBatchSchema() {
        ResourceDatabasePopulator populator = new ResourceDatabasePopulator(
                new ClassPathResource("org/springframework/batch/core/schema-h2.sql")
        );
        populator.setContinueOnError(true); // ignore if schema already initialized
        populator.execute(dataSource);
    }

    @Test
    void importsLocalCsvIntoH2() throws Exception {
        JobParameters params = new JobParametersBuilder()
                .addString("run.id", UUID.randomUUID().toString())
                .toJobParameters();

        JobExecution execution = jobLauncher.run(localJob, params);

        assertThat(execution.getExitStatus()).isEqualTo(ExitStatus.COMPLETED);
        assertThat(customerRepository.count()).isEqualTo(8);
        assertThat(customerRepository.findAll())
                .extracting(Customer::getEmail)
                .contains("john.doe@example.com", "jane.smith@example.com");
    }
}
