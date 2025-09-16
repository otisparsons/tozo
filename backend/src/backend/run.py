from quart import Quart

from backend.blueprints.control import blueprint as control_blueprint

from quart import ResponseReturnValue

from backend.lib.api_error import APIError

from quart_auth import QuartAuth
from quart_rate_limiter import RateLimiter
from quart_rate_limiter import RateLimitExceeded
from quart_schema import QuartSchema
from quart_schema import RequestSchemaValidationError
from quart_db import QuartDB
import os
from subprocess import call # nosec
from urllib.parse import urlparse
import logging

app = Quart(__name__)
app.config.from_prefixed_env(prefix="TOZO")

app.register_blueprint(control_blueprint)

@app.errorhandler(APIError) #type: ignore
async def handle_api_error(error: APIError) -> ResponseReturnValue: return {"code": error.code}, error.status_code

@app.errorhandler(500)
async def handle_generic_error(error: Exception) -> ResponseReturnValue: return {"code": "INTERNAL_SERVER_ERROR"}, 500

auth_manager = QuartAuth(app)

rate_limiter = RateLimiter(app)

@app.errorhandler(RateLimitExceeded) # type: ignore

async def handle_rate_limit_exceeded_error(
    error: RateLimitExceeded,
) -> ResponseReturnValue:
    return {}, error.get_headers(), 429

schema = QuartSchema(app, convert_casing=True)

@app.errorhandler(RequestSchemaValidationError) # type: ignore
async def handle_request_validation_error(
    error: RequestSchemaValidationError,
) -> ResponseReturnValue:
    if isinstance(error.validation_error, TypeError):
        return {"errors": str(error.validation_error)}, 400
    else:
        return {"errors": error.validation_error.json()}, 400
    
    quart_db = QuartDB(app)

@app.cli.command("recreate_db")
def recreate_db() -> None:
    db_url = urlparse(os.environ["TOZO_QUART_DB_DATABASE_URL"])
    call( #nosec
        ["psql", "-U", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_url.path.removeprefix('/')}" ],
    )
    call( #nosec
        ["psql", "-U", "postgres", "-c", f"DROP USER IF EXISTS {db_url.username}"],
    )
    call( #nosec
        ["psql", "-U", "postgres", "-c", f"CREATE USER {db_url.username} LOGIN PASSWORD '{db_url.password}' CREATEDB"],
    )
    call( #nosec
        ["psql", "-U", "postgres", "-c", f"CREATE DATABASE {db_url.path.removeprefix('/')}"]
    )

    logging.basicConfig(level=logging.INFO)
