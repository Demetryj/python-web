import asyncio
from datetime import datetime, timedelta
from typing import Any, Protocol

from aiohttp import ClientConnectionError, ClientError, ClientSession

JSON = dict[str, Any]


class HttpError(Exception):
    """Raised when an HTTP request fails or returns an invalid response."""

    pass


class CurrencyNotFoundError(Exception):
    """Raised when a requested currency code is not present in API data."""

    pass


class ExchangeRateProvider(Protocol):
    """Abstract provider contract for loading exchange rates by date."""

    async def fetch_rates_by_date(self, date: str) -> JSON:
        """Return raw exchange-rate data for the specified date."""

        ...


class PrivatBankClient:
    """Aiohttp-based client for PrivatBank exchange-rate API."""

    def __init__(self, session: ClientSession, base_url: str) -> None:
        """Store an already-configured HTTP session."""

        self.session = session
        self.base_url = base_url

    async def fetch_rates_by_date(self, date: str="") -> JSON:
        """Fetch and return raw API response for one date or current date."""

        url = f"{self.base_url}{date}" if date else self.base_url
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise HttpError(f"Error status: {response.status} for {url}")
                return await response.json()
        except (ClientConnectionError, ClientError, asyncio.TimeoutError) as err:
            raise HttpError(f"Connection error. {err}") from err
        except Exception as err:
            raise HttpError(f"Unexpected error: {err}") from err



class CurrencyService:
    """Business logic for validating and shaping currency history output."""

    DEFAULT_CURRENCIES = {"EUR", "USD"}

    def __init__(self, provider: ExchangeRateProvider) -> None:
        """Inject an exchange-rate provider dependency."""

        self.provider = provider

    @staticmethod
    def get_dates_for_query(days: int) -> list[str]:
        """Build list of previous dates (without today) in dd.mm.YYYY format."""

        now = datetime.now()
        return [
            (now - timedelta(days=day)).strftime("%d.%m.%Y")
            for day in range(1, days + 1)
        ]

    @staticmethod
    def validate_requested_currencies(
        data: JSON, extra_currencies: set[str] | None = None
    ) -> None:
        """Validate custom currency codes against available API currencies."""

        if not extra_currencies:
            return

        available_currencies = {
            item.get("currency")
            for item in data.get("exchangeRate", [])
            if item.get("currency")
        }
        unknown_currencies = extra_currencies - available_currencies

        if unknown_currencies:
            unknown_str = ", ".join(sorted(unknown_currencies))
            raise CurrencyNotFoundError(f"Currency not found: {unknown_str}")

    @staticmethod
    def adapt_response(data: JSON, currencies: set[str]) -> JSON:
        """Convert raw day data to the expected output structure."""

        currencies_by_date: JSON = {}

        for item in data.get("exchangeRate", []):
            code = item.get("currency")
            if code in currencies:
                currencies_by_date[code] = {
                    "sale": item.get("saleRate", item.get("saleRateNB")),
                    "purchase": item.get("purchaseRate", item.get("purchaseRateNB")),
                }

        return {data["date"]: currencies_by_date}

    async def fetch_history(self, days: int, extra_currencies: set[str]=set()) -> list[JSON]:
        """Fetch and return currency history for requested period and codes."""

        dates = self.get_dates_for_query(days)
        target_currencies = self.DEFAULT_CURRENCIES | extra_currencies

        # Validate extra currencies once to avoid repeated errors for every day request.
        first_day_data = await self.provider.fetch_rates_by_date(dates[0])
        self.validate_requested_currencies(first_day_data, extra_currencies)

        tasks = [self.provider.fetch_rates_by_date(date) for date in dates]
        raw_results = await asyncio.gather(*tasks)

        return [self.adapt_response(day_data, target_currencies) for day_data in raw_results]