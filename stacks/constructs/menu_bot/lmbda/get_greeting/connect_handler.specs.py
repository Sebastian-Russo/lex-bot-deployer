import json
import os
import pytest
from unittest.mock import patch

# Set environment variable for testing
os.environ['CONFIG'] = json.dumps({
    "en_US": {
        "greeting": "Thank you for calling the non-emergency hotline. How may I help you?",
        "more_prompt": "Is there anything else I can help you with?",
        "help": "I can assist with various services. Please tell me what you need.",
        "hang_up": "Thank you for calling. Goodbye."
    }
})

# Import after setting environment variable
# Adjust the import path based on your project structure
from stacks.lmbda.l2_constructs.menu_bot.connect_handler import ConnectHandler, ConnectEvent

def test_should_get_greeting():
    # Create the system under test (sut)
    sut = ConnectHandler.create()

    # Create the test event
    event = {
        "Details": {
            "ContactData": {
                "Attributes": {
                    "lang": "en_US"
                },
                "LanguageCode": "en-US"
            },
            "Parameters": {
                "lang": "en_US"
            }
        }
    }

    # Call the handler
    response = sut.handler(event)

    # Assert the response matches expected output
    assert response["greeting"] == "Thank you for calling the non-emergency hotline. How may I help you?"
    assert response["morePrompt"] == "Is there anything else I can help you with?"
    assert response["help"] == "I can assist with various services. Please tell me what you need."
    assert response["hangUp"] == "Thank you for calling. Goodbye."

def test_should_use_language_code_when_no_parameter():
    # Create the system under test
    sut = ConnectHandler.create()

    # Create test event with language code but no lang parameter
    event = {
        "Details": {
            "ContactData": {
                "LanguageCode": "en-US"
            },
            "Parameters": {}
        }
    }

    # Call the handler
    response = sut.handler(event)

    # Verify it used the language code properly
    assert response["greeting"] == "Thank you for calling the non-emergency hotline. How may I help you?"

def test_should_handle_missing_configuration():
    # Create test with non-existent language
    sut = ConnectHandler.create()

    event = {
        "Details": {
            "ContactData": {
                "LanguageCode": "fr-FR"
            },
            "Parameters": {
                "lang": "fr_FR"
            }
        }
    }

    # Should return empty strings for missing config
    response = sut.handler(event)
    assert response["greeting"] == ""
    assert response["morePrompt"] == ""
    assert response["help"] == ""
    assert response["hangUp"] == ""

def test_should_handle_missing_event_data():
    # Test with minimal event
    sut = ConnectHandler.create()

    # Empty event
    event = {}

    # Should default to en_US
    response = sut.handler(event)
    assert response["greeting"] == "Thank you for calling the non-emergency hotline. How may I help you?"