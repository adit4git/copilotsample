# JPA Mapping Templates

## Entity Example
```java
@Entity
@Table(name="ORDERS")
public class Order {
  @Id
  @Column(name="ORDER_ID")
  private Long id;
}
```

## Repository Example
```java
public interface OrderRepository extends JpaRepository<Order, Long> {}
```

## Custom Query Example
```java
@Query("SELECT o FROM Order o WHERE o.customerId = :customerId")
List<Order> getOrders(@Param("customerId") Long customerId);
```
