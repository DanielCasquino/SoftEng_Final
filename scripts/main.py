from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from sqlmodel import select

from scripts.model import User, Event, Ticket
from scripts.database import create_db_and_tables, SessionDep

import logging

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


# sanity check
@app.get("/", responses={200: {"description": "Ticket API is working"}})
async def read_root():
    """
    Sanity Check Endpoint

    Returns a simple message to verify the API is working :)

    Returns:
        dict: A message indicating the API status
    """
    return JSONResponse(status_code=200, content={"message": "Ticket API is working!"})
