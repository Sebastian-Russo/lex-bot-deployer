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
                code_hook=CodeHook(
                    lambda_=self.lambda_handler,
                    dialog_code_hook=True,
                    fulfillment_code_hook=True,
                ),
                intents=[
                    SimpleIntent(
                        intent_id='ProcessPamphletRequest',
                        name='ProcessPamphletRequest',
                        slots=[
                            SimpleSlot(
                                slot_id='pamphlet_type',
                                name='pamphlet_type',
                                slot_type='PamphletType',
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
