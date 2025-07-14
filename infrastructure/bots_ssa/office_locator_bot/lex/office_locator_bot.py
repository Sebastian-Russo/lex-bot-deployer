# pylint: disable=import-error
import os
from typing import List, Optional

# pylint: disable=import-error
from aws_cdk import aws_iam as iam
from constructs import Construct

# pylint: disable=import-error
from ....constructs.simple_bot import (
    CodeHook,
    SimpleBot,
    SimpleBotProps,
    SimpleIntent,
    SimpleLocale,
    SimpleSlot,
)

# pylint: disable=import-error
from ....utils.create_lambda import create_lambda


class OfficeLocatorBot(Construct):
    """Office Locator Bot"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        agent_transfer_queue_arn: str,
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        idle_session_ttl_in_seconds: Optional[int] = 300,
        nlu_confidence_threshold: Optional[float] = 0.75,
        log_group=None,
        audio_bucket=None,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        bot_name = f'{prefix}-office-locator'

        lambda_role = iam.Role(
            self,
            'LambdaRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaBasicExecutionRole'
                ),
            ],
        )

        # Lex Permissions (for testing)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'lex:RecognizeText',
                    'lex:PostContent',
                    'lex:PostText',
                ],
                resources=['*'],
            )
        )

        # Create Lambda function for handling dialog and fulfillment
        self.lambda_handler = create_lambda(
            self,
            'LambdaHandler',
            os.path.join(os.path.dirname(__file__), '..', 'lambdas'),
            function_name=f'{bot_name}-handler',
            description=f'Handles office locator conversation flow for {bot_name}',
            environment={
                # Add any environment variables needed for office lookup API
                'OFFICE_API_ENDPOINT': 'https://api.ssa.gov/offices',  # Example
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
                    # Main intent for locating office
                    SimpleIntent(
                        name='LocateOffice',
                        utterances=[
                            'find an office',
                            'office locations',
                            'office information',
                            'I need an office near me',
                            'office near {zipCode}',
                            'find office in {zipCode}',
                            'help me find an office',
                            'office lookup',
                            'locate office',
                            'office locator',
                            'change zip code',
                            'different zip code',
                            'new zip code',
                            'search somewhere else',
                            'look somewhere else',
                        ],
                        slots=[
                            SimpleSlot(
                                name='zipCode',
                                slot_type_name='AMAZON.Number',
                                elicitation_messages=['Placeholder'],
                                description='Five digit zip code for office search',
                                required=True,
                                max_retries=3,
                                allow_interrupt=True,
                            ),
                            # P1118: Zipcode confirmation (conditional)
                            SimpleSlot(
                                name='confirmZip',
                                slot_type_name='AMAZON.Confirmation',
                                elicitation_messages=['Placeholder'],
                                description='Confirmation of entered zip code',
                                required=False,  # Conditional based on validation
                                max_retries=2,
                                allow_interrupt=True,
                            ),
                            # P1121: Card center question (conditional)
                            SimpleSlot(
                                name='needsCard',
                                slot_type_name='AMAZON.Confirmation',
                                elicitation_messages=['Placeholder'],
                                description='Whether user needs Social Security card',
                                required=False,  # Only asked if card center available
                                max_retries=2,
                                allow_interrupt=True,
                            ),
                            # P1123: Next action choice (conditional)
                            SimpleSlot(
                                name='nextAction',
                                slot_type_name='AMAZON.AlphaNumeric',
                                elicitation_messages=['Placeholder'],
                                description='What user wants to do next',
                                required=False,  # Asked after providing office info
                                max_retries=2,
                                allow_interrupt=True,
                            ),
                        ],
                    ),
                    # Utility intents
                    SimpleIntent(
                        name='LocalOfficeInfo',
                        utterances=[
                            'local office',
                            'local office information',
                            'tell me about local office',
                            'local office info',
                        ],
                    ),
                    SimpleIntent(
                        name='Finished',
                        utterances=[
                            'I am finished',
                            'finished',
                            'done',
                            'that is all',
                            'thank you',
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
                or 'Helps users find SSA office locations by zip code',
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
