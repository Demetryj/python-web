"""FastAPI application entry point for the Contacts API."""

import logging

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.db import get_db
from src.routes import auth, contacts, users

logger = logging.getLogger(__name__)

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a normalized response for request validation errors.

    :param request: Incoming request that failed validation.
    :type request: Request
    :param exc: Validation exception raised by FastAPI.
    :type exc: RequestValidationError
    :return: JSON response with validation details.
    :rtype: JSONResponse
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.errors(),
            "message": "Bad Request",
        },
    )
    

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")


@app.get("/")
def index():
    """Return a basic application status message.

    :return: Application welcome message.
    :rtype: dict[str, str]
    """
    return {"message": "Contacts Application"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """Check database connectivity.

    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``500 Internal Server Error`` when the
        database check fails.
    :return: Health check success message.
    :rtype: dict[str, str]
    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1 + 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except SQLAlchemyError:
        logger.exception("Healthcheck database query failed")
        raise HTTPException(status_code=500, detail="Error connecting to the database")
