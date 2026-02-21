from behave import given, when, then
from gherkin_testcontainers import use_container


@given("a fresh SQLite database")
@use_container("sqlite")
def step_fresh_db(context, sqlite_client):
    context.db = sqlite_client


@when("I create a users table")
def step_create_table(context):
    context.db.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    context.db.commit()


@when('I insert a user "{name}"')
def step_insert_user(context, name):
    context.db.execute("INSERT INTO users (name) VALUES (?)", (name,))
    context.db.commit()


@then('the users table should contain "{name}"')
def step_check_user(context, name):
    row = context.db.execute(
        "SELECT name FROM users WHERE name = ?", (name,)
    ).fetchone()
    assert row is not None, f"User '{name}' not found"
    assert row[0] == name
