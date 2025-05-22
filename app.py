#!/usr/bin/env python3

import os
from aws_cdk import App, Environment
from stacks.lex_stack import LexStack

app = App()
prefix = 'lex-deploy-demo-py'

LexStack(app, 'LexPy',
    prefix=prefix,
    env=Environment(
        account='857240696749',
        region='us-east-1'
    ),
    connect_instance_arn='arn:aws:connect:us-east-1:857240696749:instance/ca082b7f-74b2-4935-8985-460415c56d14',
    city_hall_queue_arn='arn:aws:connect:us-east-1:857240696749:instance/ca082b7f-74b2-4935-8985-460415c56d14/queue/5787a8fc-42cf-40b6-8180-9cb2150446b9',
    city_manager_flow_arn='arn:aws:connect:us-east-1:857240696749:instance/ca082b7f-74b2-4935-8985-460415c56d14/contact-flow/c07ddbba-4788-4853-90be-8eea2fa57f37'
)

app.synth()