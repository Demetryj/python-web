import json
import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosedOK

from classes_ import (
    PrivatBankClient,
    CurrencyService,
    CurrencyNotFoundError,
    HttpError,
)

JSON = dict[str, Any]
COMMAND = "exchange"
MIN_DAYS = 1
MAX_DAYS = 10

BASE_URL_CURRENT_DATE = (
    "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5"
)
BASE_URL_BY_DATE = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

logging.basicConfig(level=logging.INFO)


class CommandService:
    """Parse websocket commands and delegate currency requests."""

    async def parse_command(self, message: str) -> JSON | None:
        """Return command result for `exchange` messages or None for plain text."""
        commands: list[str] = message.split()

        if not len(commands):
            return

        if len(commands) == 1:
            if commands[0] == COMMAND:
                try:
                    return await self.fetch_currency_rate(BASE_URL_CURRENT_DATE)
                except (HttpError, CurrencyNotFoundError, ValueError) as err:
                    return {"error": str(err)}
        elif len(commands) >= 2:
            if commands[0] == COMMAND and commands[1].isnumeric():
                days_for_query = int(commands[1])
                if not (MIN_DAYS <= days_for_query <= MAX_DAYS):
                    return {
                        "error": (
                            f"The number of days must be greater than 0 and no more than {MAX_DAYS}."
                        )
                    }
                try:
                    return await self.fetch_currency_rate_by_date(
                        BASE_URL_BY_DATE, days_for_query
                    )
                except (HttpError, CurrencyNotFoundError, ValueError) as err:
                    return {"error": str(err)}
        else:
            pass

    async def fetch_currency_rate(self, base_url: str):
        """Fetch current exchange rates from the provided endpoint."""
        timeout = ClientTimeout(total=10)

        async with ClientSession(timeout=timeout) as session:
            client = PrivatBankClient(session, base_url)
            data = await client.fetch_rates_by_date()
            return data

    async def fetch_currency_rate_by_date(self, base_url: str, days_for_query: int):
        """Fetch exchange-rate history for the requested number of days."""
        if not (MIN_DAYS <= days_for_query <= MAX_DAYS):
            raise ValueError(
                f"The number of days must be greater than 0 and no more than {MAX_DAYS}."
            )

        timeout = ClientTimeout(total=10)

        async with ClientSession(timeout=timeout) as session:
            client = PrivatBankClient(session, base_url)
            service = CurrencyService(client)
            result = await service.fetch_history(days_for_query)
            return result


class Server:
    """Manage websocket clients and broadcast chat or command responses."""

    clients: set[ServerConnection] = set()

    def register(self, ws: ServerConnection) -> None:
        """Register a newly connected websocket client."""
        self.clients.add(ws)
        logging.info("%s connects", ws.remote_address)

    def unregister(self, ws: ServerConnection) -> None:
        """Remove a disconnected websocket client."""
        self.clients.discard(ws)
        logging.info("%s disconnects", ws.remote_address)

    async def send_to_clients(self, message: str):
        """Broadcast a message to all connected clients."""
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def distrubute(self, ws: ServerConnection):
        """Read client messages and broadcast either command output or plain text."""

        async for message in ws:
            srevice = CommandService()
            data = await srevice.parse_command(message)
            print(data)

            if data is None:
                await self.send_to_clients(message)
                continue

            await self.send_to_clients(json.dumps(data, ensure_ascii=False, indent=4))

    async def ws_handler(self, ws: ServerConnection):
        """Handle websocket lifecycle for one client connection."""
        self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            self.unregister(ws)
