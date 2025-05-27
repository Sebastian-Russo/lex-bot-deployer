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
    SimpleSlotType,
    SimpleSlotTypeValue,
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
        city_hall_queue_arn: str,  # For agent transfers
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
                'AGENT_QUEUE_ARN': city_hall_queue_arn,
            },
        )

        # Define slot types
        slot_types = [
            SimpleSlotType(
                name='YesNoType',
                values=[
                    SimpleSlotTypeValue(
                        'yes', ['yes', 'yeah', 'yep', 'correct', 'right']
                    ),
                    SimpleSlotTypeValue('no', ['no', 'nope', 'incorrect', 'wrong']),
                ],
            ),
            SimpleSlotType(
                name='PrivacyChoiceType',
                values=[
                    SimpleSlotTypeValue(
                        'more_info', ['more information', 'more info', 'tell me more']
                    ),
                    SimpleSlotTypeValue(
                        'continue', ['continue', 'proceed', 'go on', 'next']
                    ),
                ],
            ),
            SimpleSlotType(
                name='SSNDigitType',
                values=[SimpleSlotTypeValue(str(i), [str(i)]) for i in range(10)],
            ),
        ]

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
                    # Initial 1099 request intent
                    SimpleIntent(
                        name='Start1099Request',
                        utterances=[
                            'I would like to print a 1099',
                            'I need to print a 1099',
                            'I need a 1099',
                            'I want my 1099',
                            'Can I get my 1099',
                        ],
                        slots=[
                            SimpleSlot(
                                name='birthDateInRange',
                                slot_type_name='YesNoType',
                                elicitation_messages=[
                                    'Are you born between December 15 and January 31?'
                                ],
                                description='Whether user was born between Dec 15 and Jan 31',
                                required=True,
                                max_retries=2,
                            )
                        ],
                    ),
                    # Intent for handling current year 1099 question
                    SimpleIntent(
                        name='CurrentYear1099',
                        utterances=[
                            'yes I want current year',
                            'current year',
                            'this year',
                            'yes current',
                        ],
                        slots=[
                            SimpleSlot(
                                name='wantCurrentYear',
                                slot_type_name='YesNoType',
                                elicitation_messages=[
                                    'Are you calling to get a replacement 1099 for the 2024 tax year?'
                                ],
                                description='Whether user wants current year 1099',
                                required=True,
                                max_retries=2,
                            )
                        ],
                    ),
                    # Intent for privacy information choice
                    SimpleIntent(
                        name='PrivacyChoice',
                        utterances=[
                            'more information',
                            'more info',
                            'continue',
                            'proceed',
                            'tell me more about privacy',
                        ],
                        slots=[
                            SimpleSlot(
                                name='privacyChoice',
                                slot_type_name='PrivacyChoiceType',
                                elicitation_messages=[
                                    'To hear detailed information about the Privacy Act or Paper Reduction Act, say more information. Otherwise, say continue.'
                                ],
                                description='User choice for privacy information',
                                required=True,
                                max_retries=2,
                            )
                        ],
                    ),
                    # Intent for terms agreement
                    SimpleIntent(
                        name='TermsAgreement',
                        utterances=[
                            'I agree',
                            'yes I agree',
                            'I understand',
                            'yes I understand',
                            'I do not agree',
                            'no I do not agree',
                        ],
                        slots=[
                            SimpleSlot(
                                name='agreeToTerms',
                                slot_type_name='YesNoType',
                                elicitation_messages=[
                                    'Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?'
                                ],
                                description='Whether user agrees to terms',
                                required=True,
                                max_retries=2,
                            )
                        ],
                    ),
                    # Intent for collecting SSN - first digit
                    SimpleIntent(
                        name='CollectSSN',
                        utterances=[
                            'my social security number is',
                            'my ssn is',
                            'zero',
                            'one',
                            'two',
                            'three',
                            'four',
                            'five',
                            'six',
                            'seven',
                            'eight',
                            'nine',
                        ],
                        slots=[
                            SimpleSlot(
                                name='ssnDigit1',
                                slot_type_name='SSNDigitType',
                                elicitation_messages=[
                                    'Please say your Social Security number one digit at a time. What is the first digit?'
                                ],
                                description='First digit of SSN',
                                required=True,
                                max_retries=3,
                            ),
                            SimpleSlot(
                                name='ssnDigit2',
                                slot_type_name='SSNDigitType',
                                elicitation_messages=['What is the second digit?'],
                                description='Second digit of SSN',
                                required=True,
                                max_retries=3,
                            ),
                            SimpleSlot(
                                name='ssnDigit3',
                                slot_type_name='SSNDigitType',
                                elicitation_messages=['What is the third digit?'],
                                description='Third digit of SSN',
                                required=True,
                                max_retries=3,
                            ),
                        ],
                    ),
                    # Intent for repeat requests
                    SimpleIntent(
                        name='RepeatRequest',
                        utterances=[
                            'repeat that',
                            'say that again',
                            'can you repeat',
                            'what did you say',
                            "I didn't hear that",
                        ],
                    ),
                    # Intent for returning to main menu
                    SimpleIntent(
                        name='ReturnToMenu',
                        utterances=[
                            'go back to main menu',
                            'return to menu',
                            'main menu',
                            'go back',
                        ],
                    ),
                ],
            ),
            # Spanish locale
            # SimpleLocale(
            #     locale_id='es_US',
            #     voice_id='Lupe',
            #     code_hook=CodeHook(
            #         lambda_=self.lambda_handler,
            #         dialog=True,
            #         fulfillment=True,
            #     ),
            #     intents=[
            #         SimpleIntent(
            #             name='Start1099Request',
            #             utterances=[
            #                 'Me gustaría imprimir un 1099',
            #                 'Necesito imprimir un 1099',
            #                 'Necesito un 1099',
            #                 'Quiero mi 1099',
            #                 'Puedo obtener mi 1099',
            #             ],
            #             slots=[
            #                 SimpleSlot(
            #                     name='birthDateInRange',
            #                     slot_type_name='YesNoType',
            #                     elicitation_messages=[
            #                         '¿Naciste entre el 15 de diciembre y el 31 de enero?'
            #                     ],
            #                     description='Whether user was born between Dec 15 and Jan 31',
            #                     required=True,
            #                     max_retries=2,
            #                 )
            #             ]
            #         ),
            #         # Add other Spanish intents as needed...
            #     ],
            # )
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
