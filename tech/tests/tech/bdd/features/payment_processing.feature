# features/payment_processing.feature

Feature: Payment Processing
  As a payment service
  I want to process payment requests
  So that customers can pay for their orders

  Scenario: Successfully create a new payment
    Given the order with ID 123 exists in the orders service
    And the order total is 100.50
    When I create a payment for order ID 123
    Then a payment should be created
    And the payment status should be "PENDING"
    And the payment amount should be 100.50

  Scenario: Get the status of an existing payment
    Given a payment exists for order ID 456
    And the payment status is "APPROVED"
    When I request the payment status for order ID 456
    Then I should receive the status "APPROVED"

  Scenario: Payment webhook updates payment status
    Given a payment exists for order ID 789
    And the payment status is "PENDING"
    When I receive a webhook update with status "APPROVED" for order ID 789
    Then the payment status should be updated to "APPROVED"

  Scenario: Attempt to create payment for non-existent order
    Given the order with ID 999 does not exist in the orders service
    When I create a payment for order ID 999
    Then I should receive an error message
    And no payment should be created

  Scenario: Attempt to get status for non-existent payment
    Given no payment exists for order ID 888
    When I request the payment status for order ID 888
    Then I should receive a "Payment not found" error