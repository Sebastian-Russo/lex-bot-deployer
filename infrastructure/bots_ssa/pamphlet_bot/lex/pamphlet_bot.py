import logging
import os
from typing import Optional

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

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class PamphletBot(Construct):
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

        bot_name = f'{prefix}-pamphlet'

        # Create Lambda function for handling dialog
        self.lambda_handler = create_lambda(
            self,
            'LambdaHandler',
            os.path.join(os.path.dirname(__file__), '..', 'lambdas'),
            function_name=f'{bot_name}-handler',
            description=f'Handles pamphlet conversation flow for {bot_name}',
            environment={
                'AGENT_QUEUE_ARN': city_hall_queue_arn,
            },
        )

        # Define locales
        locales = [
            SimpleLocale(
                locale_id='en_US',
                engine='neural',
                voice_id='Joanna',
                code_hook=CodeHook(
                    lambda_=self.lambda_handler,
                    dialog=True,
                    fulfillment=True,
                ),
                intents=[
                    SimpleIntent(
                        name='ProcessPamphletRequest',
                        utterances=[
                            'pamphlet',
                            'pamphlets',
                            'pamphlet on',
                            'order pamphlet',
                            'mail pamphletpamphlet on understanding social security',
                            'pamphlet on retirement benefits',
                            'pamphlet on disability benefits',
                            'pamphlet on survivor benefits',
                            'pamphlet on how work affects benefits',
                            'pamphlet on benefits for children with disabilities',
                            'pamphlet on what every woman should know about social security',
                        ],
                        slots=[
                            # Phamphlet slots
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='UnderstandingSocialSecurity',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on Understanding Social Security',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='RetirementBenefits',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on Retirement Benefits',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='DisabilityBenefits',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on Disability Benefits',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='SurvivorBenefits',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on Survivor Benefits',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='HowWorkAffectsBenefits',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on How Work Affects Benefits',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='BenefitsForChildrenWithDisabilities',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on Benefits for Children with Disabilities',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='WhatEveryWomanShouldKnowAboutSocialSecurity',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet on What Every Woman Should Know About Social Security',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            # Confirmation slots
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='HearAllChoicesAgain',
                                elicitation_messages=['Placeholder'],
                                description='Pamphlet choices again',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='HearNextPamphletChoiceConfirmation',
                                elicitation_messages=['Placeholder'],
                                description='Hear next pamphlet choice confirmation',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.AlphaNumeric',
                                name='Finished',
                                elicitation_messages=['Placeholder'],
                                description='Finished selecting',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            # Address slots
                            SimpleSlot(
                                slot_type_name='AMAZON.StreetName',
                                name='StreetName',
                                elicitation_messages=['Placeholder'],
                                description='Street name',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.City',
                                name='City',
                                elicitation_messages=['Placeholder'],
                                description='City',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.State',
                                name='State',
                                elicitation_messages=['Placeholder'],
                                description='State',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Number',
                                name='ZipCode',
                                elicitation_messages=['Placeholder'],
                                description='Zip code',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='AddressConfirmation',
                                elicitation_messages=['Placeholder'],
                                description='Address confirmation',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                        ],
                    ),
                    SimpleIntent(
                        name='Skip',
                        utterances=[
                            'skip',
                            'skip pamphlet',
                            'skip this one',
                            'next pamphlet',
                            'next',
                            'pass',
                            'pass on this one',
                        ],
                        slots=[
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='SkipPamphlet',
                                elicitation_messages=['Placeholder'],
                                description='Skip pamphlet',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                        ],
                    ),
                    SimpleIntent(
                        name='Repeat',
                        utterances=[
                            'repeat',
                            'repeat that',
                            'repeat again',
                            'say it again',
                            'tell me again',
                        ],
                        slots=[
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='RepeatRequest',
                                elicitation_messages=['Placeholder'],
                                description='Repeat request',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                        ],
                    ),
                    SimpleIntent(
                        name='ReturnToMenu',
                        utterances=[
                            'return to menu',
                            'go back to menu',
                            'main menu',
                            'return to main menu',
                            'go back to main menu',
                        ],
                        slots=[
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='ConfirmationMainMenu',
                                elicitation_messages=['Placeholder'],
                                description='Confirmation to return to main menu',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                        ],
                    ),
                    SimpleIntent(
                        name='AgentRequest',
                        utterances=[
                            'agent',
                            'agent please',
                            'speak to an agent',
                            'representative',
                            'speak to a representative',
                        ],
                        slots=[
                            SimpleSlot(
                                slot_type_name='AMAZON.Confirmation',
                                name='SpeakToAgent',
                                elicitation_messages=['Placeholder'],
                                description='Speak to agent',
                                required=False,
                                allow_interrupt=True,
                                max_retries=2,
                            ),
                        ],
                    ),
                ],
            ),
        ]

        # Create bot
        SimpleBot(
            self,
            'Bot',
            props=SimpleBotProps(
                name=bot_name,
                description=description,
                role=role,
                idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
                nlu_confidence_threshold=nlu_confidence_threshold,
                log_group=log_group,
                audio_bucket=audio_bucket,
                connect_instance_arn=connect_instance_arn,
                locales=locales,
            ),
            # slot_types=slot_types,
            # intents=intents,
        )
