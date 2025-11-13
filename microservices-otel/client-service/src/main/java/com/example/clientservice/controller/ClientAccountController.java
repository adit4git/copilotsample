package com.example.clientservice.controller;

import com.example.clientservice.model.BankAccount;
import com.example.clientservice.service.AccountClientService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class ClientAccountController {

    private static final Logger log = LoggerFactory.getLogger(ClientAccountController.class);

    private final AccountClientService accountClientService;

    public ClientAccountController(AccountClientService accountClientService) {
        this.accountClientService = accountClientService;
    }

    @GetMapping("/client/accounts")
    public List<BankAccount> getClientAccounts() {
        log.info("HTTP GET /client/accounts invoked in client-service");
        List<BankAccount> accounts = accountClientService.getAccountsFromAccountService();
        log.info("Returning {} accounts from client-service", accounts.size());
        return accounts;
    }
}
