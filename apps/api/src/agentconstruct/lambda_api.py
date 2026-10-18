"""AWS Lambda entry point for the FastAPI control plane."""

from mangum import Mangum

from agentconstruct.main import app

handler = Mangum(app, lifespan="auto", api_gateway_base_path=None)
