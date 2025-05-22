from aws_cdk import aws_lex as lex
from aws_cdk import aws_connect as connect
from aws_cdk import Aws
from constructs import Construct
from dataclasses import dataclass


# Keep the props class for backward compatibility
@dataclass
class AssociateLexBotProps:
    """
    Properties for associating a Lex bot with a Connect instance
    """

    connect_instance_arn: str
    alias: lex.CfnBotAlias


class AssociateLexBot(connect.CfnIntegrationAssociation):
    """
    Associate a Lex alias with a Connect instance
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        connect_instance_arn: str = None,
        alias: lex.CfnBotAlias = None,
        props: AssociateLexBotProps = None,
    ):
        # Support both styles - props object or individual parameters
        if props:
            connect_instance_arn = props.connect_instance_arn
            alias = props.alias

        if not connect_instance_arn or not alias:
            raise ValueError(
                'Either props or both connect_instance_arn and alias must be provided'
            )

        super().__init__(
            scope,
            id,
            instance_id=connect_instance_arn,
            integration_type='LEX_BOT',
            integration_arn=alias.attr_arn,
        )
