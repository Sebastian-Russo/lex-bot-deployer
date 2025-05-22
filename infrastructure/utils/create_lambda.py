from aws_cdk import aws_lambda as lambda_
from constructs import Construct


def create_lambda(scope: Construct, id: str, code_path: str):
    stage = scope.node.try_get_context('stage') or 'dev'

    LOGGING_LEVEL = 'ERROR' if stage == 'prod' else 'DEBUG'

    return lambda_.Function(
        scope,
        id,
        runtime=lambda_.Runtime.PYTHON_3_9,
        handler='index.handler',
        code=lambda_.Code.from_asset(code_path),
        environment={'LOGGING_LEVEL': LOGGING_LEVEL},
    )
