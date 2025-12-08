package com.example.batchmultidb.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.*;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Optional;

@Slf4j
@RestController
@RequestMapping("/jobs")
@RequiredArgsConstructor
public class CustomerJobController {

    private final JobLauncher jobLauncher;

    @Qualifier("s3ImportCustomersJob")
    private final Optional<Job> s3ImportCustomersJob;

    @Qualifier("oracleImportCustomersJob")
    private final Optional<Job> oracleImportCustomersJob;

    @Qualifier("localImportCustomersJob")
    private final Optional<Job> localImportCustomersJob;

    @PostMapping("/import-customers")
    public String triggerJob() throws Exception {
        // Try local -> oracle -> s3 depending on active mode
        Job jobToRun = localImportCustomersJob
                .or(() -> oracleImportCustomersJob)
                .or(() -> s3ImportCustomersJob)
                .orElseThrow(() -> new IllegalStateException("No import job configured"));

        JobParameters params = new JobParametersBuilder()
                .addString("run.id", Instant.now().toString())
                .toJobParameters();

        JobExecution execution = jobLauncher.run(jobToRun, params);
        log.info("Job started with ID: {} and name: {}", execution.getJobId(), jobToRun.getName());
        return "Job started with ID: " + execution.getJobId() + " (Job: " + jobToRun.getName() + ")";
    }

    @PostMapping("/import-customers-s3")
    public String triggerS3Job() throws Exception {
        Job job = s3ImportCustomersJob.orElseThrow(() -> 
            new IllegalStateException("S3 import job not available. Ensure batch.mode=s3 is configured.")
        );

        JobParameters params = new JobParametersBuilder()
                .addString("run.id", Instant.now().toString())
                .toJobParameters();

        JobExecution execution = jobLauncher.run(job, params);
        log.info("S3 job started with ID: {}", execution.getJobId());
        return "S3 Job started with ID: " + execution.getJobId();
    }

    @PostMapping("/import-customers-oracle")
    public String triggerOracleJob() throws Exception {
        Job job = oracleImportCustomersJob.orElseThrow(() ->
                new IllegalStateException("Oracle import job not available. Ensure batch.mode=oracle is configured.")
        );

        JobParameters params = new JobParametersBuilder()
                .addString("run.id", Instant.now().toString())
                .toJobParameters();

        JobExecution execution = jobLauncher.run(job, params);
        log.info("Oracle job started with ID: {}", execution.getJobId());
        return "Oracle Job started with ID: " + execution.getJobId();
    }

    @PostMapping("/import-customers-local")
    public String triggerLocalJob() throws Exception {
        Job job = localImportCustomersJob.orElseThrow(() -> 
            new IllegalStateException("Local import job not available. Ensure batch.mode=local is configured.")
        );

        JobParameters params = new JobParametersBuilder()
                .addString("run.id", Instant.now().toString())
                .toJobParameters();

        JobExecution execution = jobLauncher.run(job, params);
        log.info("Local job started with ID: {}", execution.getJobId());
        return "Local Job started with ID: " + execution.getJobId();
    }
}
