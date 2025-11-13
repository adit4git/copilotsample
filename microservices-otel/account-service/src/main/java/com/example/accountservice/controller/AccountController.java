package com.example.accountservice.controller;

import com.example.accountservice.model.BankAccount;
import com.example.accountservice.service.BankAccountService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class AccountController {

    private static final Logger log = LoggerFactory.getLogger(AccountController.class);

    private final BankAccountService bankAccountService;

    public AccountController(BankAccountService bankAccountService) {
        this.bankAccountService = bankAccountService;
    }

    @GetMapping("/accounts")
    public List<BankAccount> getAccounts() {
        log.info("HTTP GET /accounts invoked");
        List<BankAccount> accounts = bankAccountService.getAllAccounts();
        log.info("Returning {} accounts", accounts.size());
        return accounts;
    }
}
