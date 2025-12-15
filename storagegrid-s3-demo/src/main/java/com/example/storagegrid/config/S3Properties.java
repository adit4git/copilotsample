package com.example.storagegrid.config;

import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "s3")
public record S3Properties(
        @NotBlank String endpoint,   // e.g. https://s3.company.com:10443  (BASE endpoint, no bucket)
        @NotBlank String region,     // any fixed region; many S3-compatible systems ignore it
        @NotBlank String accessKey,
        @NotBlank String secretKey,
        @NotBlank String bucket,
        boolean pathStyle,           // true is often required for StorageGRID unless endpoint domain names are configured
        boolean chunkedEncoding,     // set false if your S3-compatible target has issues with chunked encoding
        boolean checksumValidation   // set false if target doesn't like checksum headers/validation
) {
}
