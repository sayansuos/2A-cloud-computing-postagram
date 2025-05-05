#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from main_serverless import ServerlessStack


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # define resources here


app = App()
# MyStack(app, "ter")
ServerlessStack(app, "cdktf_serverless")

app.synth()
