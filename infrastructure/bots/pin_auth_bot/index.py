import os
from typing import List, Optional

from aws_cdk import aws_iam as iam
from constructs import Construct

from ...constructs.simple_bot import (
    CodeHook,
    SimpleBot,
    SimpleBotProps,
    SimpleIntent,
    SimpleLocale,
    SimpleSlot,
)
from ...utils.create_lambda import create_lambda


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
        log_group=None,
        audio_bucket=None,
        **kwargs,
    ):
        super().__init__(scope, id)

        # Create the Lambda function
        self.lambda_function = create_lambda(
            self, 'Lambda', os.path.join(os.path.dirname(__file__), 'handler')
        )

        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id='en_US',
                voice_id='Joanna',
                code_hook=CodeHook(
                    lambda_=self.lambda_function,
                    fulfillment=True,
                ),
                intents=[
                    SimpleIntent(
                        name='AccountNumber',
                        utterances=[
                            'My account number is {accountId}',
                            'My account id is {accountId}',
                            'It is {accountId}',
                            'Hello',
                            'Are you there?',
                            'What am I supposed to do?',
                        ],
                        slots=[
                            SimpleSlot(
                                name='accountId',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'May I have your Account Number?',
                                    'What is your Account Number?',
                                ],
                                max_retries=3,
                                allow_interrupt=True,
                                required=True,
                            ),
                            SimpleSlot(
                                name='accountPin',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'Can you please provide me your PIN number?'
                                ],
                                max_retries=3,
                                allow_interrupt=True,
                                required=True,
                            ),
                        ],
                    ),
                ],
            )
        ]

        # Create bot
        self.bot = SimpleBot(
            self,
            'Bot',
            props=SimpleBotProps(
                name=f'{prefix}-pin-auth',
                description=description,
                role=role,
                idle_session_ttl_in_seconds=300,
                nlu_confidence_threshold=0.75,
                log_group=log_group,
                audio_bucket=audio_bucket,
                connect_instance_arn=connect_instance_arn,
                locales=locales,
            ),
        )
