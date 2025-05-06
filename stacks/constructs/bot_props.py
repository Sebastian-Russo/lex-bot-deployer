from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from dataclasses import dataclass
from typing import Optional

@dataclass
class BotProps:
    """Properties for creating a Lex bot"""
    prefix: str
    connect_instance_arn: str
    role: Optional[iam.IRole] = None
    log_group: Optional[logs.ILogGroup] = None
    audio_bucket: Optional[s3.IBucket] = None