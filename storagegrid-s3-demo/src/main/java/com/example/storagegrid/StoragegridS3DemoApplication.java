package com.example.storagegrid;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class StoragegridS3DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(StoragegridS3DemoApplication.class, args);
    }
}
