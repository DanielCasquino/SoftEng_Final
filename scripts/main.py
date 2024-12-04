from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from sqlmodel import select

from scripts.model import User, Event, Ticket, TicketStatus
from scripts.database import create_db_and_tables, SessionDep
import os
import logging
from datetime import datetime


logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logger():
    log_filename = os.path.join(logs_dir, f"log_{datetime.now().strftime('%d_%m_%Y')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()



@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)



@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Method: {request.method}, URL: {request.url}, IP: {request.client.host}")

    response = await call_next(request)

    logger.info(f"State: {response.status_code}")

    return response
# sanity check


@app.get("/count_logs")
async def count_logs():
    logs_files = os.listdir(logs_dir)


    positive_count = 0
    negative_count = 0

    for log_file in logs_files:
        logs = []
        with open(os.path.join(logs_dir, log_file), 'r') as f:
            logs.extend(f.readlines())

        for log in logs:

            if "Execution successful" in log:
                positive_count += 1
            elif "Execution failed" in log:
                negative_count += 1
    return {"successes": positive_count, "fails": negative_count}

@app.get("/", responses={200: {"description": "Ticket API is working"}})
async def read_root():
    """
    Sanity Check

    Returns a simple message to verify the API is working :)

    Returns:
        dict: A message indicating the API status
    """
    return JSONResponse(status_code=200, content={"message": "Ticket API is working!"})


# Creates a user
@app.post(
    "/user",
    response_model=User,
    responses={
        201: {"description": "User created", "model": User},
        400: {"description": "Invalid username"},
    },
)
async def create_user(session: SessionDep, user: User) -> User:
    """
    User Registration

    Receives a user object, creates it in the database, and returns it.

    Args:
        user (object): The user object to create

    Returns:
        user (object): The created user as a UserDTO object

    Raises:
        400: If the username is invalid
    """
    try:
        if not user.username:
            return JSONResponse(status_code=400, content={"message": "Invalid username"})
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Execution successful")
        return JSONResponse(status_code=201, content=user.model_dump())
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        logger.error("Execution failed")
        return JSONResponse(status_code=500, content={"message": "Internal server error"})


# Retrieves a user with a given id
@app.get(
    "/user/{user_id}",
    response_model=User,
    responses={
        200: {"description": "User found", "model": User},
        404: {"description": "User not found"},
    },
)
async def get_user(session: SessionDep, user_id: int) -> User:
    """
    User Get

    Retrieves a user with a given id from the database.

    Args:
        user_id (int): The id of the user to retrieve

    Returns:
        user (object): The user with the desired id

    Raises:
        404: If the user is not found
    """
    user = await session.get(User, user_id)
    if user is None:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    return JSONResponse(status_code=200, content=user.model_dump())


@app.get(
    "/user",
    response_model=list[User],
    responses={
        200: {"description": "Users found", "model": list[User]},
    },
)
async def get_all_users(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[User]:
    """
    User Get All

    Retrieves all users from the database.

    Returns:
        users (list): A list of all users

    """
    users = await session.execute(select(User).offset(offset).limit(limit))
    users = users.scalars().all()
    return JSONResponse(status_code=200, content=[user.model_dump() for user in users])


@app.post(
    "/event",
    response_model=Event,
    responses={
        201: {"description": "Event created", "model": Event},
        400: {"description": "Invalid event name"},
    },
)
async def create_event(session: SessionDep, event: Event) -> Event:
    """
    Event Creation

    Receives an event object, creates it in the database, and returns it.

    Args:
        event (object): The event object to create

    Returns:
        event (object): The created event

    Raises:
        400: If the event name is invalid
    """
    if not event.name:
        return JSONResponse(status_code=400, content={"message": "Invalid event name"})
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return JSONResponse(status_code=201, content=event.model_dump())


@app.get(
    "/event/{event_id}",
    response_model=Event,
    responses={
        200: {"description": "Event found", "model": Event},
        404: {"description": "Event not found"},
    },
)
async def get_event(session: SessionDep, event_id: int) -> Event:
    """
    Event Get

    Retrieves an event with a given id from the database.

    Args:
        event_id (int): The id of the event to retrieve

    Returns:
        event (object): The event with the desired id

    Raises:
        404: If the event is not found
    """
    event = await session.get(Event, event_id)
    if event is None:
        return JSONResponse(status_code=404, content={"message": "Event not found"})
    return JSONResponse(status_code=200, content=event.model_dump())


@app.get(
    "/event",
    response_model=list[Event],
    responses={
        200: {"description": "Events found", "model": list[Event]},
    },
)
async def get_all_events(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Event]:
    """
    Event Get All

    Retrieves all events from the database.

    Returns:
        events (list): A list of all events

    """
    events = await session.execute(select(Event).offset(offset).limit(limit))
    events = events.scalars().all()
    return JSONResponse(
        status_code=200, content=[event.model_dump() for event in events]
    )


@app.patch(
    "/ticket/use/{ticket_id}",
    response_model=Ticket,
    responses={
        200: {"description": "Ticket marked as used", "model": Ticket},
        404: {"description": "Ticket not found"},
        402: {"description": "Ticket must be paid to be used"},
        400: {"description": "Ticket is already used or canceled"},
    },
)
async def use_ticket(session: SessionDep, ticket_id: int) -> Ticket:
    """
    Ticket Use

    Marks a ticket as used.

    Args:
        ticket_id (int): The id of the ticket to mark as used

    Returns:
        ticket (object): The ticket with the desired id, now marked as used

    Raises:
        404: If the ticket is not found
    """
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        return JSONResponse(status_code=404, content={"message": "Ticket not found"})

    if ticket.status == TicketStatus.RESERVED:
        return JSONResponse(
            status_code=402, content={"message": "Ticket must be paid to be used"}
        )

    if ticket.status == TicketStatus.USED:
        return JSONResponse(
            status_code=400, content={"message": "Ticket is already used"}
        )

    if ticket.status == TicketStatus.CANCELED:
        return JSONResponse(
            status_code=400, content={"message": "Ticket is canceled, cannot be used"}
        )

    ticket.status = TicketStatus.USED
    await session.commit()
    return JSONResponse(status_code=200, content=ticket.model_dump())


@app.post(
    "/ticket/buy/{user_id}/{event_id}",
    response_model=Ticket,
    responses={
        201: {"description": "Ticket created", "model": Ticket},
        404: {"description": "User or event not found"},
    },
)
async def buy_ticket(session: SessionDep, user_id: int, event_id: int) -> Ticket:
    """
    Ticket Purchase

    Creates a ticket for a user for a given event.

    Args:
        user_id (int): The id of the user to purchase the ticket for
        event_id (int): The id of the event to purchase the ticket for

    Returns:
        ticket (object): The created ticket

    Raises:
        400: If the ticket is invalid
    """
    user = await session.get(User, user_id)
    event = await session.get(Event, event_id)

    if user is None or event is None:
        return JSONResponse(
            status_code=404, content={"message": "User or event not found"}
        )
    ticket = Ticket(user_id=user_id, event_id=event_id, status=TicketStatus.PURCHASED)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return JSONResponse(status_code=201, content=ticket.model_dump())


@app.post(
    "/ticket/reserve/{user_id}/{event_id}",
    response_model=Ticket,
    responses={
        200: {"description": "Ticket reserved", "model": Ticket},
        404: {"description": "User or event not found"},
    },
)
async def reserve_ticket(session: SessionDep, user_id: int, event_id: int) -> Ticket:
    """
    Ticket Reservation

    Marks a ticket as reserved.

    Args:
        ticket_id (int): The id of the ticket to mark as reserved

    Returns:
        ticket (object): The ticket with the desired id, now marked as reserved

    Raises:
        404: If the ticket is not found
    """
    user = await session.get(User, user_id)
    event = await session.get(Event, event_id)

    if user is None or event is None:
        return JSONResponse(
            status_code=404, content={"message": "User or event not found"}
        )

    ticket = Ticket(user_id=user_id, event_id=event_id, status=TicketStatus.RESERVED)

    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return JSONResponse(status_code=200, content=ticket.model_dump())


@app.patch(
    "/ticket/pay/{ticket_id}",
    response_model=Ticket,
    responses={
        200: {"description": "Ticket paid", "model": Ticket},
        404: {"description": "Ticket not found"},
        400: {"description": "Ticket is already paid or used or canceled"},
    },
)
async def pay_ticket(session: SessionDep, ticket_id: int) -> Ticket:
    """
    Ticket Payment

    Marks a ticket as paid.

    Args:
        ticket_id (int): The id of the ticket to mark as paid

    Returns:
        ticket (object): The ticket with the desired id, now marked as paid

    Raises:
        404: If the ticket is not found
    """
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        return JSONResponse(status_code=404, content={"message": "Ticket not found"})

    if ticket.status == TicketStatus.PURCHASED:
        return JSONResponse(
            status_code=400, content={"message": "Ticket is already paid for"}
        )

    if ticket.status == TicketStatus.USED:
        return JSONResponse(
            status_code=400, content={"message": "Ticket is already used"}
        )

    if ticket.status == TicketStatus.CANCELED:
        return JSONResponse(
            status_code=400, content={"message": "Ticket is canceled, cannot be paid"}
        )

    ticket.status = TicketStatus.PURCHASED
    await session.commit()
    await session.refresh(ticket)
    return JSONResponse(status_code=200, content=ticket.model_dump())


@app.patch(
    "/ticket/cancel/{ticket_id}",
    response_model=Ticket,
    responses={
        200: {"description": "Ticket canceled", "model": Ticket},
        404: {"description": "Ticket not found"},
        400: {"description": "Ticket is already canceled"},
    },
)
async def cancel_ticket(session: SessionDep, ticket_id: int) -> Ticket:
    """
    Ticket Cancel

    Marks a ticket as canceled.

    Args:
        ticket_id (int): The id of the ticket to mark as canceled

    Returns:
        ticket (object): The ticket with the desired id, now marked as canceled

    Raises:
        404: If the ticket is not found
    """
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        return JSONResponse(status_code=404, content={"message": "Ticket not found"})

    if ticket.status == TicketStatus.CANCELED:
        return JSONResponse(
            status_code=400, content={"message": "Ticket is already canceled"}
        )

    if ticket.status == TicketStatus.USED:
        return JSONResponse(
            status_code=400,
            content={"message": "Ticket is already used, cannot be canceled"},
        )

    ticket.status = TicketStatus.CANCELED
    await session.commit()
    return JSONResponse(status_code=200, content=ticket.model_dump())
