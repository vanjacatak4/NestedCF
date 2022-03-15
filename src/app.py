from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType, Response
from aws_lambda_powertools.event_handler.exceptions import NotFoundError

tracer = Tracer()
logger = Logger()
app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEventV2)


@app.get("/hello")
@tracer.capture_method
def get_hello_message():
    print(app.__dict__)
    return 5


@app.get("/admin")
@tracer.capture_method
def get_admin_message():
    print(app.__dict__)
    return 55


@app.get("/su")
@tracer.capture_method
def get_su_message():
    print(app.__dict__)
    return 505


@app.get("/both")
@tracer.capture_method
def get_both_message():
    print(app.__dict__)
    return 50555


@app.not_found
@tracer.capture_method
def handle_not_found_errors(exc: NotFoundError) -> Response:
    # Return 418 upon 404 errors
    logger.info(f"Not found route: {app.current_event.path}")
    return Response(
        status_code=418,
        content_type=content_types.TEXT_PLAIN,
        body="I'm a teapot!"
    )


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
