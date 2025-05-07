import os
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk import aws_iam as iam
from ..constructs.simple_bot import SimpleBot
from typing import Optional

class PinAuthBot(Construct):
    """
    Verify a caller by collecting personal information and comparing it with a DB via fulfillment lambda
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
        self.lambda_function = PythonFunction(
            self, 'Lambda',
            entry=os.path.join(os.path.dirname(__file__), 'lambda'),  # Assuming you'll create a 'lambda' directory with your handler
            index='handler.py',  # The Python file name
            handler='handler',   # The function name
            environment={
                'LOGGING_LEVEL': 'debug'
            }
        )

        # Create bot
        self.bot = SimpleBot(
            self, 'Bot',
            name=f"{prefix}-pin-auth",
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
                            "name": "AccountNumber",
                            "utterances": [
                                'My account number is {accountId}',
                                'My account id is {accountId}',
                                'It is {accountId}',
                                '{accountId}'
                            ],
                            "slots": [
                                {
                                    "name": "accountId",
                                    "slot_type_name": "AMAZON.AlphaNumeric",
                                    "elicitation_messages": [
                                        'May I have your Account Number?',
                                        'What is your Account Number?'
                                    ],
                                    "required": True
                                },
                                {
                                    "name": "accountPin",
                                    "slot_type_name": "AMAZON.AlphaNumeric",
                                    "elicitation_messages": [
                                        'Can you please provide me your PIN number?'
                                    ],
                                    "required": True
                                }
                            ]
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