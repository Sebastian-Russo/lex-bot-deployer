from constructs import Construct
from ..constructs.simple_bot import SimpleBot
from aws_cdk import aws_iam as iam
from typing import Optional

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
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs
    ):
        # Create locales with Yes/No intents
        locales = [
            {
                "locale_id": "en_US",
                "voice_id": "Joanna",
                "intents": [
                    {
                        "name": "Yes",
                        "utterances": [
                            'yeah', 'yep', 'yea', 'yes', 'all right',
                            'surely', 'yes sir', 'of course', 'absolutely',
                            'for sure', 'totally', 'correct', 'si'
                        ],
                    },
                    {
                        "name": "No",
                        "utterances": [
                            'nope', 'nah', 'no', 'never', 'no thanks',
                            'no way', 'absolutely not', 'no thank you', 'dont'
                        ],
                    }
                ]
            },
            {
                "locale_id": "es_US",
                "voice_id": "Lupe",
                "intents": [
                    {
                        "name": "Yes",
                        "utterances": [
                            'sí', 'claro', 'por supuesto', 'correcto', 'totalmente',
                            'absolutamente', 'afirmativo'
                        ],
                    },
                    {
                        "name": "No",
                        "utterances": [
                            'no', 'no gracias', 'no gracias', 'no thank you',
                            'no way', 'absolutamente no', 'ni hablar', 'de ninguna manera',
                            'no es posible'
                        ],
                    }
                ]
            }
        ]

        # Ensure we have valid default values
        if idle_session_ttl_in_seconds is None:
            idle_session_ttl_in_seconds = 300  # Default to 5 minutes
        if nlu_confidence_threshold is None:
            nlu_confidence_threshold = 0.75  # Default to 75%

        super().__init__(
            scope, id,
            name=f"{prefix}-yes-no",
            description=description,
            locales=locales,
            role=role,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            nlu_confidence_threshold=nlu_confidence_threshold,
            log_group=log_group,
            audio_bucket=audio_bucket,
            **kwargs
        )