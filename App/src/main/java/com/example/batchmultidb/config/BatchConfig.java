package com.example.batchmultidb.config;

import com.example.batchmultidb.batch.*;
import com.example.batchmultidb.datasource.ConnectionFactory;
import com.example.batchmultidb.domain.Customer;
import com.example.batchmultidb.repository.CustomerRepository;
import com.example.batchmultidb.repository.oracle.CustomerOracleRepository;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.EnableBatchProcessing;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.transaction.PlatformTransactionManager;
import software.amazon.awssdk.services.s3.S3Client;
import lombok.extern.slf4j.Slf4j;

@Configuration
@EnableBatchProcessing
@Slf4j
public class BatchConfig {

    @Value("${aws.s3.bucket-name}")
    private String bucketName;

    @Value("${aws.s3.key}")
    private String key;

    @Value("${local.csv.path:classpath:data/customers.csv}")
    private String localCsvPath;

    @Autowired
    private ResourceLoader resourceLoader;

    // ============ S3 Mode Beans ============

    @Bean
    @ConditionalOnProperty(name = "batch.mode", havingValue = "s3")
    public ItemStreamReader<Customer> s3CustomerItemReader(S3Client s3Client) {
        log.info("Using S3 item reader with bucket: {} and key: {}", bucketName, key);
        return new S3CustomerItemReader(s3Client, bucketName, key);
    }

    @Bean
    @ConditionalOnProperty(name = "batch.mode", havingValue = "s3")
    public ItemWriter<Customer> s3CustomerItemWriter(
            CustomerOracleRepository oracleRepository,
            ConnectionFactory connectionFactory) {
        log.info("Using S3 multi-DB item writer (Oracle + H2)");
        return new MultiDbCustomerItemWriter(oracleRepository, connectionFactory);
    }

    @Bean(name = "oracleCustomerItemWriter")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "oracle")
    public ItemWriter<Customer> oracleCustomerItemWriter(CustomerOracleRepository oracleRepository) {
        log.info("Using Oracle-only item writer");
        return new OracleDbCustomerItemWriter(oracleRepository);
    }

    @Bean(name = "s3CustomerImportStep")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "s3")
    public Step s3CustomerImportStep(JobRepository jobRepository,
                                     PlatformTransactionManager transactionManager,
                                     ItemStreamReader<Customer> reader,
                                     ItemProcessor<Customer, Customer> processor,
                                     ItemWriter<Customer> writer) {
        return new StepBuilder("s3CustomerImportStep", jobRepository)
                .<Customer, Customer>chunk(100, transactionManager)
                .reader(reader)
                .processor(processor)
                .writer(writer)
                .build();
    }

    @Bean(name = "s3ImportCustomersJob")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "s3")
    public Job s3ImportCustomersJob(JobRepository jobRepository,
                                    Step s3CustomerImportStep) {
        return new JobBuilder("s3ImportCustomersJob", jobRepository)
                .start(s3CustomerImportStep)
                .build();
    }

    // ============ Local CSV Mode Beans ============

    @Bean
    @ConditionalOnProperty(name = "batch.mode", havingValue = "local", matchIfMissing = true)
    public ItemStreamReader<Customer> localCsvCustomerItemReader() {
        Resource resource = resourceLoader.getResource(localCsvPath);
        log.info("Using local CSV item reader from: {}", localCsvPath);
        return new LocalCsvCustomerItemReader(resource);
    }

    @Bean
    @ConditionalOnProperty(name = "batch.mode", havingValue = "oracle")
    public ItemStreamReader<Customer> oracleCsvCustomerItemReader() {
        Resource resource = resourceLoader.getResource(localCsvPath);
        log.info("Using local CSV item reader (Oracle mode) from: {}", localCsvPath);
        return new LocalCsvCustomerItemReader(resource);
    }

    @Bean
    @ConditionalOnProperty(name = "batch.mode", havingValue = "local", matchIfMissing = true)
    public ItemWriter<Customer> localDbCustomerItemWriter(CustomerRepository customerRepository) {
        log.info("Using local DB item writer (H2 only)");
        return new LocalDbCustomerItemWriter(customerRepository);
    }

    @Bean(name = "localCustomerImportStep")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "local", matchIfMissing = true)
    public Step localCustomerImportStep(JobRepository jobRepository,
                                        PlatformTransactionManager transactionManager,
                                        ItemStreamReader<Customer> reader,
                                        ItemProcessor<Customer, Customer> processor,
                                        ItemWriter<Customer> writer) {
        return new StepBuilder("localCustomerImportStep", jobRepository)
                .<Customer, Customer>chunk(100, transactionManager)
                .reader(reader)
                .processor(processor)
                .writer(writer)
                .build();
    }

    @Bean(name = "oracleCustomerImportStep")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "oracle")
    public Step oracleCustomerImportStep(JobRepository jobRepository,
                                         PlatformTransactionManager transactionManager,
                                         ItemStreamReader<Customer> reader,
                                         ItemProcessor<Customer, Customer> processor,
                                         @Qualifier("oracleCustomerItemWriter") ItemWriter<Customer> writer) {
        return new StepBuilder("oracleCustomerImportStep", jobRepository)
                .<Customer, Customer>chunk(100, transactionManager)
                .reader(reader)
                .processor(processor)
                .writer(writer)
                .build();
    }

    @Bean(name = "localImportCustomersJob")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "local", matchIfMissing = true)
    public Job localImportCustomersJob(JobRepository jobRepository,
                                       Step localCustomerImportStep) {
        return new JobBuilder("localImportCustomersJob", jobRepository)
                .start(localCustomerImportStep)
                .build();
    }

    @Bean(name = "oracleImportCustomersJob")
    @ConditionalOnProperty(name = "batch.mode", havingValue = "oracle")
    public Job oracleImportCustomersJob(JobRepository jobRepository,
                                        Step oracleCustomerImportStep) {
        return new JobBuilder("oracleImportCustomersJob", jobRepository)
                .start(oracleCustomerImportStep)
                .build();
    }

    // ============ Shared Beans ============

    @Bean
    public ItemProcessor<Customer, Customer> customerItemProcessor() {
        return new CustomerItemProcessor();
    }
}
