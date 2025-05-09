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
                            "slotTypeName": "AMAZON.Number",
                            "valueElicitationSetting": {
                                "slotConstraint": "Required",
                                "promptSpecification": {
                                    "messageGroupsList": [
                                        {
                                            "message": {
                                                "plainTextMessage": {
                                                    "value": "What is the house or building?"
                                                }
                                            }
                                        }
                                    ],
                                    "maxRetries": 3
                                }
                            }
                        },
                        {
                            "name": "streetName",
                            "slotTypeName": "AMAZON.AlphaNumeric",
                            "valueElicitationSetting": {
                                "slotConstraint": "Required",
                                "promptSpecification": {
                                    "messageGroupsList": [
                                        {
                                            "message": {
                                                "plainTextMessage": {
                                                    "value": "What is the street name?"
                                                }
                                            }
                                        }
                                    ],
                                    "maxRetries": 3
                                }
                            }
                        },
                        {
                            "name": "city",
                            "slotTypeName": "AMAZON.City",
                            "valueElicitationSetting": {
                                "slotConstraint": "Required",
                                "promptSpecification": {
                                    "messageGroupsList": [
                                        {
                                            "message": {
                                                "plainTextMessage": {
                                                    "value": "What is the city?"
                                                }
                                            }
                                        }
                                    ],
                                    "maxRetries": 3
                                }
                            }
                        },
                        {
                            "name": "state",
                            "slotTypeName": "AMAZON.State",
                            "valueElicitationSetting": {
                                "slotConstraint": "Required",
                                "promptSpecification": {
                                    "messageGroupsList": [
                                        {
                                            "message": {
                                                "plainTextMessage": {
                                                    "value": "What is the state?"
                                                }
                                            }
                                        }
                                    ],
                                    "maxRetries": 3
                                }
                            }
                        },
                        {
                            "name": "zipCode",
                            "slotTypeName": "AMAZON.Number",
                            "valueElicitationSetting": {
                                "slotConstraint": "Required",
                                "promptSpecification": {
                                    "messageGroupsList": [
                                        {
                                            "message": {
                                                "plainTextMessage": {
                                                    "value": "What is the zip code?"
                                                }
                                            }
                                        }
                                    ],
                                    "maxRetries": 3
                                }
                            }}
                        ]
                    },

                    {
                        "name": "Agent",
                        "utterances": ['Speak to an agent', 'Talk to a human', 'I need human help']
                    },

                    # Required fallback intent
                    {
                        "name": "FallbackIntent",
                        "description": "Default intent when no other intent matches",
                        "parentIntentSignature": "AMAZON.FallbackIntent",
                        "utterances": []
                    }
                ]
            }
        ]
    )




