package com.example.clientservice.service;

import com.example.clientservice.model.BankAccount;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.List;

@Service
public class AccountClientService {

    private static final Logger log = LoggerFactory.getLogger(AccountClientService.class);

    private final WebClient webClient;
    private final String accountServiceBaseUrl;
    private final MeterRegistry meterRegistry;

    public AccountClientService(WebClient.Builder webClientBuilder,
                                @Value("${account-service.base-url}") String accountServiceBaseUrl,
                                MeterRegistry meterRegistry) {
        this.webClient = webClientBuilder.baseUrl(accountServiceBaseUrl).build();
        this.accountServiceBaseUrl = accountServiceBaseUrl;
        this.meterRegistry = meterRegistry;
    }

    public List<BankAccount> getAccountsFromAccountService() {
        Timer.Sample sample = Timer.start(meterRegistry);

        log.info("Calling account-service at {}/accounts", accountServiceBaseUrl);

        try {
            Mono<BankAccount[]> mono = webClient.get()
                    .uri("/accounts")
                    .retrieve()
                    .bodyToMono(BankAccount[].class);

            BankAccount[] array = mono.block();

            List<BankAccount> accounts = array != null ? Arrays.asList(array) : List.of();
            log.info("Received {} accounts from account-service", accounts.size());

            return accounts;
        } finally {
            sample.stop(
                    Timer.builder("client_service.accounts.fetch.timer")
                            .description("Time taken to call account-service and fetch accounts")
                            .register(meterRegistry)
            );
            meterRegistry.counter("client_service.accounts.fetch.count").increment();
        }
    }
}
