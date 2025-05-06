#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from main_serverless import ServerlessStack
from main_server import ServerStack


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # define resources here


app = App()
# MyStack(app, "ter")
ServerlessStack(app, "cdktf_serverless")
ServerStack(app, "cdktf_server")
app.synth()
