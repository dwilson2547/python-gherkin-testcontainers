Feature: SQLite CRUD operations

  Scenario: Create a table and insert a record
    Given a fresh SQLite database
    When I create a users table
    And I insert a user "Alice"
    Then the users table should contain "Alice"
