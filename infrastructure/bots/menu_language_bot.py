from typing import List, Optional

from aws_cdk import aws_iam as iam
from constructs import Construct

from ..constructs.simple_bot import (
    SimpleBot,
    SimpleBotProps,
    SimpleIntent,
    SimpleLocale,
)


class MenuLanguageBot(SimpleBot):
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
        # Create locales with language selection intents
        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id='en_US',
                voice_id='Joanna',
                intents=[
                    SimpleIntent(
                        name='Spanish',
                        utterances=['spanish', 'espanol', 'espanyol'],
                    ),
                    SimpleIntent(
                        name='English',
                        utterances=['english', 'ingles'],
                    ),
                ],
            ),
            SimpleLocale(
                locale_id='es_US',
                voice_id='Lupe',
                intents=[
                    SimpleIntent(
                        name='Spanish',
                        utterances=['spanish', 'espanol', 'espanyol'],
                    ),
                    SimpleIntent(
                        name='English',
                        utterances=['english', 'ingles'],
                    ),
                ],
            ),
        ]

        super().__init__(
            scope,
            id,
            props=SimpleBotProps(
                name=f'{prefix}-menu-language',
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
