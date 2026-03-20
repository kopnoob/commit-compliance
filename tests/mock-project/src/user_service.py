"""User service with test fixtures containing real-looking PII."""

import json

# FIXME: Replace with proper test fixtures
TEST_USERS = [
    {
        "name": "Kari Nordmann",
        "email": "kari.nordmann@gmail.com",
        "phone": "+47 912 34 567",
        "ssn": "01019000083",  # Norwegian fødselsnummer
        "account": "1234 56 78901",  # Bank account
    },
    {
        "name": "Ola Hansen",
        "email": "ola.hansen@outlook.com",
        "phone": "+47 481 23 456",
        "ssn": "15037800071",
        "account": "9876 54 32109",
    },
]


def get_user_by_ssn(ssn: str) -> dict | None:
    """Look up user by fødselsnummer."""
    for user in TEST_USERS:
        if user["ssn"] == ssn:
            return user
    return None


def format_user_display(user: dict) -> str:
    """Format user info for display — should mask PII in production!"""
    return f"{user['name']} ({user['email']}) — {user['phone']}"
