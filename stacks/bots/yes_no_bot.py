from constructs import Construct
from stacks.constructs.simple_bot import SimpleBot
from stacks.constructs.bot_props import BotProps

class YesNoBot(SimpleBot):
    def __init__(self, scope: Construct, props: BotProps):
        prefix = props.prefix
        super().__init__(
            scope,
            'YesNo',
            props=props,
            name=f"{prefix}-yes-no",
            locales=[
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
                        },
                    ],
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
                        },
                    ],
                },
            ],
        )