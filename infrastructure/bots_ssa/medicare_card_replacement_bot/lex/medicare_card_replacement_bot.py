import os
from typing import Any, Dict, List

from constructs import Construct

from ....constructs.simple_bot import (
    CodeHook,
    SimpleBot,
    SimpleBotProps,
    SimpleIntent,
    SimpleLocale,
    SimpleSlot,
)
from ....utils.create_lambda import create_lambda


class LexHelper:
    """Helper class for working with Lex V2 events and responses"""

    def __init__(self, event: Dict[str, Any]):
        self.event = event
        self.session_attributes = (
            event.get('sessionState', {}).get('sessionAttributes', {}) or {}
        )

    @property
    def intent_name(self) -> str:
        return self.event.get('sessionState', {}).get('intent', {}).get('name', '')

    @property
    def slots(self) -> Dict[str, Any]:
        return (
            self.event.get('sessionState', {}).get('intent', {}).get('slots', {}) or {}
        )

    def clear_slot(self, slot_name: str) -> None:
        if slot_name in self.slots:
            self.slots[slot_name] = None

    def delegate(self) -> Dict[str, Any]:
        return {
            'sessionState': {
                'dialogAction': {'type': 'Delegate'},
                'intent': self.event['sessionState']['intent'],
                'sessionAttributes': self.session_attributes,
            }
        }

    def elicit_slot(self, slot_name: str, message: str = None) -> Dict[str, Any]:
        response = {
            'sessionState': {
                'dialogAction': {'type': 'ElicitSlot', 'slotToElicit': slot_name},
                'intent': self.event['sessionState']['intent'],
                'sessionAttributes': self.session_attributes,
            }
        }
        if message:
            response['messages'] = [{'contentType': 'PlainText', 'content': message}]
        return response

    def elicit_intent(self, message: str) -> Dict[str, Any]:
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': self.session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def fulfilled_response(self, message: str) -> Dict[str, Any]:
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': self.intent_name, 'state': 'Fulfilled'},
                'sessionAttributes': self.session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def failed_response(self, message: str) -> Dict[str, Any]:
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': self.intent_name, 'state': 'Failed'},
                'sessionAttributes': self.session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }


class MedicareCardReplacementBot(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        # city_hall_queue_arn: str,
        # description: Optional[str] = None,
        # role: Optional[iam.IRole] = None,
        # idle_session_ttl_in_seconds: Optional[int] = 300,
        # nlu_confidence_threshold: Optional[float] = 0.75,
        # log_group=None,
        # audio_bucket=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        bot_name = f'{prefix}-medicare-card-replacement'

        # Create Lambda handler
        self.lambda_handler = create_lambda(
            self,
            'LambdaHandler',
            os.path.join(os.path.dirname(__file__), '..', 'lambdas'),
            function_name=f'{bot_name}-handler',
            description='Handles Medicare card replacement conversation flow',
            environment={},
        )

        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id='en_US',
                voice_id='Joanna',
                code_hook=CodeHook(
                    lambda_=self.lambda_handler,
                    dialog=True,  # Controls slot collection flow
                    fulfillment=True,  # Handles API calls and final responses
                ),
                intents=[
                    # Main intent for Medicare card replacement process
                    SimpleIntent(
                        name='ProcessMedicareCardReplacement',
                        utterances=[
                            'medicare card replacement',
                            'replace medicare card',
                            'need new medicare card',
                            'lost medicare card',
                            'medicare replacement',
                            'medicare card',
                            'replacement medicare card',
                            'get medicare card',
                            'new medicare card',
                            'medicare',
                            'I need a medicare card',
                            'I lost my medicare card',
                            'medicare card request',
                            'request medicare card',
                        ],
                        slots=[
                            SimpleSlot(
                                name='privacyAcknowledgment',
                                slot_type_name='AMAZON.Confirmation',
                                elicitation_messages=['Placeholder'],
                                description='User choice to continue or get more privacy information',
                                required=False,  # Dialog hook controls when to ask
                                max_retries=2,
                                allow_interrupt=True,
                            ),
                            SimpleSlot(
                                name='termsAgreement',
                                slot_type_name='AMAZON.Confirmation',
                                elicitation_messages=['Placeholder'],
                                description='User agreement to terms and conditions',
                                required=False,  # Only asked after privacy acknowledgment
                                max_retries=2,
                                allow_interrupt=True,
                            ),
                            # Authentication slots - collected conditionally
                            SimpleSlot(
                                name='socialSecurityNumber',
                                slot_type_name='AMAZON.Number',
                                elicitation_messages=['Placeholder'],
                                description='Social Security Number for verification',
                                required=False,  # Only after terms agreement
                                max_retries=3,
                                allow_interrupt=True,
                            ),
                            SimpleSlot(
                                name='dateOfBirth',
                                slot_type_name='AMAZON.Date',
                                elicitation_messages=['Placeholder'],
                                description='Date of birth for verification',
                                required=False,  # Only after SSN success
                                max_retries=3,
                                allow_interrupt=True,
                            ),
                            SimpleSlot(
                                name='firstName',
                                slot_type_name='AMAZON.FirstName',
                                elicitation_messages=['Placeholder'],
                                description='First name for verification',
                                required=False,  # Only after DOB success
                                max_retries=3,
                                allow_interrupt=True,
                            ),
                            SimpleSlot(
                                name='lastName',
                                slot_type_name='AMAZON.LastName',
                                elicitation_messages=['Placeholder'],
                                description='Last name for verification',
                                required=False,  # Only after first name success
                                max_retries=3,
                                allow_interrupt=True,
                            ),
                        ],
                    ),
                    # Supporting intent for privacy information
                    SimpleIntent(
                        name='MorePrivacyInformation',
                        utterances=[
                            'more information',
                            'privacy act information',
                            'paperwork reduction act',
                            'tell me more',
                            'privacy information',
                        ],
                    ),
                    # Utility intents
                    SimpleIntent(
                        name='ReturnToMenu',
                        utterances=[
                            'go back to main menu',
                            'return to menu',
                            'main menu',
                            'go back',
                        ],
                    ),
                    SimpleIntent(
                        name='Finished',
                        utterances=[
                            'I am finished',
                            'finished',
                            'done',
                            'that is all',
                            'hang up',
                        ],
                    ),
                ],
            ),
        ]

        # Create the bot
        self.bot = SimpleBot(
            self,
            'Bot',
            props=SimpleBotProps(
                name=bot_name,
                description='Helps users request replacement Medicare cards through automated verification',
                locales=locales,
                connect_instance_arn=connect_instance_arn,
            ),
        )
