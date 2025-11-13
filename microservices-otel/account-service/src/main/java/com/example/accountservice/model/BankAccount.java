package com.example.accountservice.model;

import java.math.BigDecimal;

public class BankAccount {
    private String id;
    private String ownerName;
    private String type;
    private BigDecimal balance;
    private String currency;

    public BankAccount(String id, String ownerName, String type, BigDecimal balance, String currency) {
        this.id = id;
        this.ownerName = ownerName;
        this.type = type;
        this.balance = balance;
        this.currency = currency;
    }

    public String getId() {
        return id;
    }

    public String getOwnerName() {
        return ownerName;
    }

    public String getType() {
        return type;
    }

    public BigDecimal getBalance() {
        return balance;
    }

    public String getCurrency() {
        return currency;
    }
}
