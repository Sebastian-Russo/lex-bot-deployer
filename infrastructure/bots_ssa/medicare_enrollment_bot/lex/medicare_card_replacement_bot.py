import os

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


class MedicareEnrollmentBot(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        city_hall_queue_arn: str,  # For agent transfers
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        bot_name = f'{prefix}-medicare-enrollment'

        # Create Lambda function for handling dialog
        self.lambda_handler = create_lambda(
            self,
            'LambdaHandler',
            os.path.join(os.path.dirname(__file__), '..', 'lambdas'),
            function_name=f'{bot_name}-handler',
            description=f'Handles medicare enrollment conversation flow for {bot_name}',
            environment={
                'AGENT_QUEUE_ARN': city_hall_queue_arn,
            },
        )

        locales = [
            SimpleLocale(
                locale_id='en_US',
                voice_id='Joanna',
                code_hook=CodeHook(
                    lambda_=self.lambda_handler,
                    dialog=True,
                    fulfillment=True,
                ),
                intents=[
                    SimpleIntent(
                        name='MedicareEnrollment',
                        utterances=['medicare enrollment', 'enrollment'],
                        slots=[
                            SimpleSlot(
                                name='Confirmation',
                                slot_type_name='AMAZON.Confirmation',
                                elicitation_messages=['Placeholder'],
                                description='Confirmation slot',
                                allow_interrupt=True,
                                max_retries=2,
                                required=False,
                            ),
                        ],
                    )
                ],
            )
        ]

        # Create the bot
        self.bot = SimpleBot(
            self,
            'Bot',
            props=SimpleBotProps(
                name=bot_name,
                description='Helps users enroll in Medicare.',
                locales=locales,
                connect_instance_arn=connect_instance_arn,
            ),
        )
