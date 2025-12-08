package com.example.batchmultidb.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.StringUtils;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3ClientBuilder;
import software.amazon.awssdk.services.s3.S3Configuration;

import java.net.URI;

@Configuration
public class S3Config {

    @Value("${aws.region}")
    private String region;

    @Value("${aws.s3.endpoint:}")
    private String endpointOverride;

    @Value("${aws.s3.path-style-access-enabled:true}")
    private boolean pathStyleAccessEnabled;

    @Bean
    public S3Client s3Client() {
        S3ClientBuilder builder = S3Client.builder()
                .region(Region.of(region))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .serviceConfiguration(S3Configuration.builder()
                        .pathStyleAccessEnabled(pathStyleAccessEnabled)
                        .chunkedEncodingEnabled(false) // helps with StorageGRID compatibility
                        .build());

        if (StringUtils.hasText(endpointOverride)) {
            builder = builder.endpointOverride(URI.create(endpointOverride));
        }

        return builder.build();
    }
}
