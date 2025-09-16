from typing import AsyncGenerator

import pytest
from quart import Quart

from backend.run import app

from quart_db import Connection

from backend.run import quart_db

@pytest.fixture(name="connection", scope="function")
async def _connection(app: Quart) -> AsyncGenerator[Connection, None]: 
    async with quart_db.connection() as connection: 
        async with connection.transaction(): yield Connection

@pytest.fixture(name="app", scope="function")
async def _app() -> AsyncGenerator[Quart, None]:
    async with app.test_app():
        yield app



        