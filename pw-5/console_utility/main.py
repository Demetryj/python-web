import asyncio
import json
import sys

from aiohttp import ClientSession, ClientTimeout

from classes_ import PrivatBankClient, CurrencyService, CurrencyNotFoundError, HttpError

BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="


def parse_args(argv: list[str]) -> tuple[int, set[str]]:
    """Parse CLI arguments: days and optional extra currency codes."""

    if len(argv) < 2 or not argv[1].isnumeric():
        raise ValueError("Usage: py main.py <days 1-10> [currency1 currency2 ...]")

    days_for_query = int(argv[1])
    if days_for_query < 1 or days_for_query > 10:
        raise ValueError(
            "The number of days must be greater than 0 and no more than 10."
        )

    extra_currencies = {currency.upper() for currency in argv[2:]}
    return days_for_query, extra_currencies


async def main() -> None:
    """CLI entrypoint: parse args, run service, print JSON output."""

    days_for_query, extra_currencies = parse_args(sys.argv)
    timeout = ClientTimeout(total=10)

    async with ClientSession(timeout=timeout) as session:
        client = PrivatBankClient(session, BASE_URL)
        service = CurrencyService(client)
        result = await service.fetch_history(days_for_query, extra_currencies)
        print(json.dumps(result, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, CurrencyNotFoundError, HttpError) as err:
        print(f"Error: {err}")
