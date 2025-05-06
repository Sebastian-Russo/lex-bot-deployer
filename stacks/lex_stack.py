from aws_cdk import Stack, RemovalPolicy
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct
from dataclasses import dataclass
from typing import Optional

# Import bot implementations
# from .bots.pin_auth_bot import PinAuthBot
# from .bots.address_change_bot import AddressChangeBot
# from .bots.agent_busy_bot import AgentBusyBot
# from .bots.menu_language_bot import MenuLanguageBot
# from .bots.office_closed_bot import OfficeClosedBot
from .bots.yes_no_bot import YesNoBot
# from .bots.non_emergency_menu_bot import NonEmergencyMenuBot
# from .bots.city_menu_bot import CityMenuBot

# Import constructs
from .constructs.lex_role import LexRole
from .constructs.throttled_deploy import throttled_deploy

# Define stack properties
@dataclass
class LexStackProps:
    prefix: str
    connect_instance_arn: str
    city_hall_queue_arn: str
    city_manager_flow_arn: str
    env: Optional[dict] = None
    stack_name: Optional[str] = None

class LexStack(Stack):
    """
    Creates the lex bots in a single stack
    TODO: Inject audioBucketName since we cant create our own buckets
    TODO: Inject encryptionKeyArn and enable audio and log group encryption
    """
    def __init__(self, scope: Construct, id: str, props: LexStackProps):
        super().__init__(
            scope,
            id,
            env=props.env,
            stack_name=props.stack_name
        )

        prefix = props.prefix
        connect_instance_arn = props.connect_instance_arn

        # Create Role
        role = LexRole(self, 'LexRole')

        # Create Audio Bucket
        audio_bucket = s3.Bucket(self, 'AudioBucket')
        audio_bucket.grant_write(role)

        # Create Log Group
        log_group = logs.LogGroup(self, 'LogGroup',
            log_group_name=f"{prefix}/lex",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Common properties for all bots
        lex_props = {
            "prefix": prefix,
            "connect_instance_arn": connect_instance_arn,
            "role": role,
            "log_group": log_group,
            "audio_bucket": audio_bucket
        }

        # Create bots with throttled deployment
        bots = [
            # Comment out all bots except YesNoBot
            # MenuLanguageBot(self, lex_props),
            YesNoBot(self, lex_props),
            # AgentBusyBot(self, lex_props),
            # OfficeClosedBot(self, lex_props),
            # AddressChangeBot(self, lex_props),
            # PinAuthBot(self, lex_props),
            # Demonstrates how to use MenuBot as call router
            # NonEmergencyMenuBot(self, lex_props),
            # CityMenuBot(self, {
            #     **lex_props,
            #     "city_hall_queue_arn": props.city_hall_queue_arn,
            #     "city_manager_flow_arn": props.city_manager_flow_arn
            # })
        ]

        # Apply throttled deployment to avoid API limits
        throttled_deploy(bots)

        # Add tags
        try:
            import importlib.metadata
            name = "lex-project-template-py"  # Your package name
            version = importlib.metadata.version(name)
        except:
            name = "lex-project-template-py"
            version = "0.1.0"

        self.tags.set_tag("Prefix", prefix)
        self.tags.set_tag("Project", name)
        self.tags.set_tag("Version", version)