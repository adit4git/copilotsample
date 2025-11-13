package com.example.accountservice.service;

import com.example.accountservice.model.BankAccount;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;

@Service
public class BankAccountService {

    private static final Logger log = LoggerFactory.getLogger(BankAccountService.class);

    private final MeterRegistry meterRegistry;

    public BankAccountService(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    public List<BankAccount> getAllAccounts() {
        Timer.Sample sample = Timer.start(meterRegistry);
        log.info("Fetching all bank accounts");

        try {
            // Mock business logic
            List<BankAccount> accounts = List.of(
                    new BankAccount("A-1001", "Alice", "CHECKING", new BigDecimal("1250.50"), "USD"),
                    new BankAccount("A-1002", "Bob", "SAVINGS", new BigDecimal("8200.00"), "USD"),
                    new BankAccount("A-1003", "Charlie", "CHECKING", new BigDecimal("300.00"), "USD")
            );
            log.debug("Number of accounts fetched: {}", accounts.size());
            return accounts;
        } finally {
            sample.stop(
                    Timer.builder("account_service.accounts.fetch.timer")
                            .description("Time taken to fetch all bank accounts")
                            .register(meterRegistry)
            );

            meterRegistry.counter("account_service.accounts.fetch.count").increment();
        }
    }
}
