import os
from typing import List, Optional

from aws_cdk import aws_iam as iam
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


class Reprint1099Bot(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        agent_transfer_queue_arn: str,  # For agent transfers
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        idle_session_ttl_in_seconds: Optional[int] = 300,
        nlu_confidence_threshold: Optional[float] = 0.75,
        log_group=None,
        audio_bucket=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        bot_name = f'{prefix}-reprint-1099'

        # Create Lambda function for handling dialog
        self.lambda_handler = create_lambda(
            self,
            'LambdaHandler',
            os.path.join(os.path.dirname(__file__), '..', 'lambdas'),
            function_name=f'{bot_name}-handler',
            description=f'Handles 1099 reprint conversation flow for {bot_name}',
            environment={
                'CURRENT_TAX_YEAR': '2024',
                'AGENT_QUEUE_ARN': agent_transfer_queue_arn,
            },
        )

        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id='en_US',
                voice_id='Joanna',
                code_hook=CodeHook(
                    lambda_=self.lambda_handler,
                    dialog=True,
                    fulfillment=True,
                ),
                intents=[
                    # Single intent handles entire conversation through sequential slots
                    SimpleIntent(
                        name='Process1099Request',
                        utterances=[
                            # Response to Connect's "Do you have a foreign address?"
                            'yes',
                            'yeah',
                            'yep',
                            'correct',
                            'right',
                            'true',
                            'si',
                            'sure',
                            'okay',
                            'no',
                            'nope',
                            'nah',
                            'incorrect',
                            'wrong',
                            'false',
                            'never',
                            # Also include generic starters
                            'help me',
                            'I need help',
                            'start',
                            'begin',
                            'hello',
                            'hi',
                        ],
                        slots=[
                            # Slot 1: Foreign address (filled by Connect prompt response)
                            SimpleSlot(
                                name='foreignAddress',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'Do you have a foreign address?'  # Backup if Connect doesn't ask
                                ],
                                description='Whether user has a foreign address',
                                required=True,
                                max_retries=2,
                            ),
                            # Slot 2: Current year (conditional)
                            SimpleSlot(
                                name='currentYear',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'Are you calling to get a replacement 1099 for the 2024 tax year?'
                                ],
                                description='Whether user wants current year 1099',
                                required=False,  # Made conditional by Lambda
                                max_retries=2,
                            ),
                            # Slot 3: Prior years (conditional)
                            SimpleSlot(
                                name='priorYears',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'Are you calling to get a replacement 1099 for any of the prior 5 years?'
                                ],
                                description='Whether user wants prior year 1099',
                                required=False,  # Made conditional by Lambda
                                max_retries=2,
                            ),
                            # Slot 4: Privacy choice (conditional)
                            SimpleSlot(
                                name='privacyChoice',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'Alright. Before I can access your records, I will need to ask a question or two to verify who you are. Social Security is allowed to collect this information under the Social Security Act, and the collection meets the requirements of the Paperwork Reduction Act under OMB numbers 09600596 and 09600583. The whole process should take about six minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say continue.'
                                ],
                                description='User choice for privacy information',
                                required=False,  # Made conditional by Lambda
                                max_retries=2,
                            ),
                            # Slot 5: Terms agreement (conditional)
                            SimpleSlot(
                                name='termsAgreement',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=[
                                    'Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?'
                                ],
                                description='Whether user agrees to terms',
                                required=False,  # Made conditional by Lambda
                                max_retries=2,
                            ),
                            # Slots 6-8: SSN Collection (conditional)
                            SimpleSlot(
                                name='ssnDigit1',
                                slot_type_name='AMAZON.Number',
                                elicitation_messages=[
                                    'Alright, thanks. Let us keep going. First, please say your Social Security number one digit at a time. What is the first digit?'
                                ],
                                description='First digit of SSN',
                                required=False,  # Made conditional by Lambda
                                max_retries=3,
                            ),
                            SimpleSlot(
                                name='ssnDigit2',
                                slot_type_name='AMAZON.Number',
                                elicitation_messages=['What is the second digit?'],
                                description='Second digit of SSN',
                                required=False,
                                max_retries=3,
                            ),
                            SimpleSlot(
                                name='ssnDigit3',
                                slot_type_name='AMAZON.Number',
                                elicitation_messages=['What is the third digit?'],
                                description='Third digit of SSN',
                                required=False,
                                max_retries=3,
                            ),
                        ],
                    ),
                    # Keep utility intents separate
                    SimpleIntent(
                        name='RepeatRequest',
                        utterances=[
                            'repeat that',
                            'say that again',
                            'can you repeat',
                            'what did you say',
                            "I didn't hear that",
                            'pardon',
                            'excuse me',
                        ],
                    ),
                    SimpleIntent(
                        name='ReturnToMenu',
                        utterances=[
                            'go back to main menu',
                            'return to menu',
                            'main menu',
                            'go back',
                            'menu',
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
                description=description
                or 'Handles SSA 1099 reprint requests with verification',
                locales=locales,
                role=role,
                idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
                nlu_confidence_threshold=nlu_confidence_threshold,
                log_group=log_group,
                audio_bucket=audio_bucket,
                connect_instance_arn=connect_instance_arn,
            ),
            **kwargs,
        )
