from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

tracer = Tracer()
logger = Logger()
app = ApiGatewayResolver()  # by default API Gateway REST API (v1)

@app.get("/<message>/<name>")
@tracer.capture_method
def get_message(message, name):
    return {"message": f"{message}, {name}"}

# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)