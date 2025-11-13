package com.example.accountservice.config;

import io.opentelemetry.exporter.zipkin.ZipkinSpanExporter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenTelemetryZipkinConfig {

    @Bean
    public ZipkinSpanExporter zipkinSpanExporter(
            @Value("${management.zipkin.tracing.endpoint:http://localhost:9411/api/v2/spans}") String zipkinEndpoint) {
        return ZipkinSpanExporter.builder()
                .setEndpoint(zipkinEndpoint)
                .build();
    }
}
