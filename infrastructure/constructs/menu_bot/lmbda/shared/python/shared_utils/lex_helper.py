from typing import Dict, Any, Optional, TypeVar, Generic, List, Union

# Create a generic type for attributes
TAttributes = TypeVar('TAttributes', bound=Dict[str, str])


class LexHelper(Generic[TAttributes]):
    """
    Simplifies lex responses
    Adapted from: https://github.com/joeykilpatrick/amazon-chime-sma-lex-demo/blob/master/lib/lambdas/reservation-bot-fulfillment/LexResponder.ts
    """

    def __init__(self, event: Dict[str, Any]):
        self.event = event
        self.session_attributes = event.get('sessionState', {}).get(
            'sessionAttributes', {}
        )

    @property
    def interpretation(self):
        """
        Returns the first interpretation
        """
        if (
            not self.event.get('interpretations')
            or len(self.event['interpretations']) == 0
        ):
            raise Exception('No interpretations found')
        return self.event['interpretations'][0]

    @property
    def slots(self):
        return self.interpretation.get('intent', {}).get('slots', {})

    @property
    def intent_name(self) -> str:
        return self.interpretation.get('intent', {}).get('name', '')

    @property
    def locale_id(self) -> str:
        return self.event.get('bot', {}).get('localeId', '')

    def slot_value(self, slot_name: str) -> Optional[str]:
        slot = self.slots.get(slot_name, {})
        if slot and 'value' in slot and 'interpretedValue' in slot['value']:
            return slot['value']['interpretedValue']
        return None

    def delegate(self) -> Dict[str, Any]:
        return {
            'sessionState': {
                'intent': self.event.get('sessionState', {}).get('intent', {}),
                'sessionAttributes': self.session_attributes,
                'dialogAction': {'type': 'Delegate'},
            }
        }

    def elicit_intent(self, message: str) -> Dict[str, Any]:
        return {
            'sessionState': {
                'sessionAttributes': self.session_attributes,
                'dialogAction': {'type': 'ElicitIntent'},
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def elicit_slot(self, slot_to_elicit: str, message: str) -> Dict[str, Any]:
        return {
            'sessionState': {
                'sessionAttributes': self.session_attributes,
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'slotToElicit': slot_to_elicit,
                    'slotElicitationStyle': 'Default',
                },
                'intent': {
                    'state': 'InProgress',
                    'name': self.intent_name,
                    'slots': self.slots,
                },
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def fulfilled_response(
        self, message: Optional[str] = None, ssml: bool = False
    ) -> Dict[str, Any]:
        """
        Let Lex know that the intent is fulfilled
        Args:
            message: If provided, message will override the fulfillmentPrompt (if available)
            ssml: Whether to use SSML for content type
        """
        result = {
            'sessionState': {
                'sessionAttributes': self.session_attributes,
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'slots': self.slots,
                    'name': self.intent_name,
                    'state': 'Fulfilled',
                },
            }
        }

        if message:
            result['messages'] = [
                {'contentType': 'SSML' if ssml else 'PlainText', 'content': message}
            ]

        return result

    def failed_response(self, message: str) -> Dict[str, Any]:
        return {
            'sessionState': {
                'sessionAttributes': self.session_attributes,
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'slots': self.slots,
                    'name': self.intent_name,
                    'state': 'Failed',
                },
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }
