from typing import Any, Dict, Optional


class LexHelper:
    """
    Helper class for working with Lex V2 events and responses
    """

    def __init__(self, event: Dict[str, Any]):
        self.event = event
        self.session_attributes = event.get('sessionState', {}).get(
            'sessionAttributes', {}
        )

    @property
    def locale_id(self) -> str:
        """Get the locale ID from the event"""
        return self.event.get('bot', {}).get('localeId', 'en_US')

    @property
    def intent_name(self) -> str:
        """Get the current intent name"""
        return self.event.get('sessionState', {}).get('intent', {}).get('name', '')

    @property
    def slots(self) -> Dict[str, Any]:
        """Get the current slots"""
        return self.event.get('sessionState', {}).get('intent', {}).get('slots', {})

    @property
    def input_transcript(self) -> str:
        """Get the user's input transcript"""
        return self.event.get('inputTranscript', '')

    def get_slot_value(self, slot_name: str) -> Optional[str]:
        """Get the interpreted value of a specific slot"""
        slot = self.slots.get(slot_name)
        if slot and slot.get('value'):
            return slot['value'].get('interpretedValue')
        return None

    def clear_slot(self, slot_name: str) -> None:
        """Clear a specific slot value"""
        if slot_name in self.slots:
            self.slots[slot_name] = None

    def delegate(self) -> Dict[str, Any]:
        """
        Delegate response - let Lex continue with the conversation
        """
        return {
            'sessionState': {
                'dialogAction': {'type': 'Delegate'},
                'intent': self.event['sessionState']['intent'],
                'sessionAttributes': self.session_attributes,
            }
        }

    def elicit_slot(self, slot_name: str, message: str = None) -> Dict[str, Any]:
        """
        Elicit a specific slot from the user
        """
        response = {
            'sessionState': {
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'slotToElicit': slot_name,
                },
                'intent': self.event['sessionState']['intent'],
                'sessionAttributes': self.session_attributes,
            }
        }

        if message:
            response['messages'] = [
                {
                    'contentType': 'PlainText',
                    'content': message,
                }
            ]

        return response

    def elicit_intent(self, message: str) -> Dict[str, Any]:
        """
        Elicit a new intent from the user
        """
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': self.session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': message,
                }
            ],
        }

    def fulfilled_response(self, message: str) -> Dict[str, Any]:
        """
        Close the conversation with a fulfillment message
        """
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'name': self.intent_name,
                    'state': 'Fulfilled',
                },
                'sessionAttributes': self.session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': message,
                }
            ],
        }

    def failed_response(self, message: str) -> Dict[str, Any]:
        """
        Close the conversation with a failed message
        """
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'name': self.intent_name,
                    'state': 'Failed',
                },
                'sessionAttributes': self.session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': message,
                }
            ],
        }

    def confirm_intent(self, message: str) -> Dict[str, Any]:
        """
        Ask for intent confirmation
        """
        return {
            'sessionState': {
                'dialogAction': {'type': 'ConfirmIntent'},
                'intent': self.event['sessionState']['intent'],
                'sessionAttributes': self.session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': message,
                }
            ],
        }
