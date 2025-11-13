package com.example.clientservice.model;

import java.math.BigDecimal;

public class BankAccount {
    private String id;
    private String ownerName;
    private String type;
    private BigDecimal balance;
    private String currency;

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

    public void setId(String id) {
        this.id = id;
    }

    public void setOwnerName(String ownerName) {
        this.ownerName = ownerName;
    }

    public void setType(String type) {
        this.type = type;
    }

    public void setBalance(BigDecimal balance) {
        this.balance = balance;
    }

    public void setCurrency(String currency) {
        this.currency = currency;
    }
}
