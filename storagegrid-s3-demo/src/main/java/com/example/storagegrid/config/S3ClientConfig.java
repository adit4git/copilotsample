package com.example.storagegrid.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.S3Client;

import java.net.URI;

@Configuration
public class S3ClientConfig {

    @Bean
    public S3Client s3Client(S3Properties props) {
        S3Configuration s3cfg = S3Configuration.builder()
                .pathStyleAccessEnabled(props.pathStyle())
                .chunkedEncodingEnabled(props.chunkedEncoding())
                .checksumValidationEnabled(props.checksumValidation())
                .build();

        return S3Client.builder()
                .endpointOverride(URI.create(props.endpoint()))
                .region(Region.of(props.region()))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(props.accessKey(), props.secretKey())
                        )
                )
                .serviceConfiguration(s3cfg)
                .build();
    }
}
