package com.example.batchmultidb.batch;

import com.example.batchmultidb.domain.Customer;
import org.springframework.batch.item.ItemProcessor;

public class CustomerItemProcessor implements ItemProcessor<Customer, Customer> {

    @Override
    public Customer process(Customer item) {
        if (item == null) {
            return null;
        }
        item.setFirstName(capitalize(item.getFirstName()));
        item.setLastName(capitalize(item.getLastName()));
        return item;
    }

    private String capitalize(String s) {
        if (s == null || s.isBlank()) return s;
        return s.substring(0, 1).toUpperCase() + s.substring(1).toLowerCase();
    }
}
