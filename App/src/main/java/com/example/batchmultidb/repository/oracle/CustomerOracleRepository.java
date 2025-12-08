package com.example.batchmultidb.repository.oracle;

import com.example.batchmultidb.domain.Customer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CustomerOracleRepository extends JpaRepository<Customer, Long> {
}
