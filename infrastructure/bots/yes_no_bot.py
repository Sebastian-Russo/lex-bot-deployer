from constructs import Construct
from ..constructs.simple_bot import SimpleBot, SimpleBotProps, SimpleLocale, SimpleIntent
from aws_cdk import aws_iam as iam
from typing import Optional, List

class YesNoBot(SimpleBot):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        idle_session_ttl_in_seconds: Optional[int] = 300,
        nlu_confidence_threshold: Optional[float] = 0.75,
        log_group=None,
        audio_bucket=None,
        **kwargs
    ):
        # Create locales with Yes/No intents
        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id="en_US",
                voice_id="Joanna",
                intents=[
                    SimpleIntent(
                        name="Yes",
                        utterances=[
                            'yeah', 'yep', 'yea', 'yes', 'all right',
                            'surely', 'yes sir', 'of course', 'absolutely',
                            'for sure', 'totally', 'correct', 'si', 'bueno'
                        ],
                    ),
                    SimpleIntent(
                        name="No",
                        utterances=[
                            'nope', 'nah', 'no', 'never', 'no thanks',
                            'no way', 'absolutely not', 'no thank you', 'dont'
                        ],
                    )
                ]
            ),
            SimpleLocale(
                locale_id="es_US",
                voice_id="Lupe",
                intents=[
                    SimpleIntent(
                        name="Yes",
                        utterances=[
                            'sí', 'claro', 'por supuesto', 'correcto', 'totalmente',
                            'absolutamente', 'afirmativo'
                        ],
                    ),
                    SimpleIntent(
                        name="No",
                        utterances=[
                            'no', 'no gracias', 'de ninguna manera', 'ni hablar',
                            'absolutamente no', 'no es posible', 'nunca'
                        ],
                    )
                ],
            ),
        ]

        super().__init__(
            scope, id,
            props=SimpleBotProps(
                name=f"{prefix}-yes-no",
                description=description,
                locales=locales,
                role=role,
                idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
                nlu_confidence_threshold=nlu_confidence_threshold,
                log_group=log_group,
                audio_bucket=audio_bucket,
                connect_instance_arn=connect_instance_arn,
            ),
            **kwargs
        )