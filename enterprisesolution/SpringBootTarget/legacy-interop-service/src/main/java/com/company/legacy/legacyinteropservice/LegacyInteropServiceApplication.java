package com.company.legacy.legacyinteropservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class LegacyInteropServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(LegacyInteropServiceApplication.class, args);
    }
}

@RestController
class HealthController {
    @GetMapping("/health")
    public String health() {
        return "legacy-interop-service OK";
    }
}
