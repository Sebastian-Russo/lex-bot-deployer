import os
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from ...constructs.simple_bot import SimpleBot
from typing import Optional

class AddressChangeBot(Construct):
    """
    Fills address change slots and calls a fulfillment lambda
    ALERT: This is more of beta/starter. You may need a custom slot type for the street.
    Sample created from: https://aws.amazon.com/blogs/contact-center/updating-your-addresses-with-amazon-connect-and-amazon-lex/
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Create the Lambda function
        self.lambda_function = lambda_.Function(
            self, 'Lambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='handler.handler',
            code=lambda_.Code.from_asset(os.path.dirname(__file__)),
            environment={
                'LOGGING_LEVEL': 'debug'
            }
        )

        # Create bot
        self.bot = SimpleBot(
            self, 'Bot',
            name=f"{prefix}-address-change",
            description=description,
            role=role,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            nlu_confidence_threshold=nlu_confidence_threshold,
            log_group=log_group,
            audio_bucket=audio_bucket,
            connect_instance_arn=connect_instance_arn,
            locales=[
                {
                    "locale_id": "en_US",
                    "voice_id": "Joanna",
                    "code_hook": {
                        "lambda_": self.lambda_function,
                        "fulfillment": True
                    },
                    "intents": [
                        {
                            "name": "AddressChange",
                            "utterances": [
                                'I would like to update my address to {houseNumber} {streetName}',
                                'I would like to update my address to {houseNumber} {streetName} {city} {state} {zipCode}',
                                'I would like to update to my new address',
                                'I would like to update address',
                                'Update address',
                                'I want to change my address',
                                'Change address',
                                'Address change',
                            ],
                            "slots": [
                                {
                                    "name": "houseNumber",
                                    "description": "House or building number",
                                    "slot_type_name": "AMAZON.Number",
                                    "elicitation_messages": ["What is the house or building?"],
                                    "max_retries": 3,
                                    "allow_interrupt": True,
                                    "required": True
                                },
                                {
                                    "name": "streetName",
                                    "description": "Street name",
                                    "slot_type_name": "AMAZON.AlphaNumeric",
                                    "elicitation_messages": ["What is the street name?"],
                                    "max_retries": 3,
                                    "allow_interrupt": True,
                                    "required": True
                                },
                                {
                                    "name": "city",
                                    "description": "City",
                                    "slot_type_name": "AMAZON.City",
                                    "elicitation_messages": ["What is the city?"],
                                    "max_retries": 3,
                                    "allow_interrupt": True,
                                    "required": True
                                },
                                {
                                    "name": "state",
                                    "description": "State",
                                    "slot_type_name": "AMAZON.State",
                                    "elicitation_messages": ["What is the state?"],
                                    "max_retries": 3,
                                    "allow_interrupt": True,
                                    "required": True
                                },
                                {
                                    "name": "zipCode",
                                    "description": "Zip code",
                                    "slot_type_name": "AMAZON.Number",
                                    "elicitation_messages": ["What is the zip code?"],
                                    "max_retries": 3,
                                    "allow_interrupt": True,
                                    "required": True
                                }
                            ]
                        },
                        {
                            "name": "Agent",
                            "utterances": ['Speak to an agent', 'Talk to a human', 'I need human help']
                        }
                        # The FallbackIntent will be added automatically by SimpleBot
                    ]
                }
        ]
    )




