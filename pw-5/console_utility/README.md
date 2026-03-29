# Console Utility: PrivatBank Exchange Rates

A console utility for getting exchange rates from the public PrivatBank API for the latest days (excluding today).

## What This Utility Does

- Returns `EUR` and `USD` rates for the last `N` days.
- Allows adding extra currencies through command-line arguments.
- Uses asynchronous requests with `aiohttp`.
- Limits the period to `1..10` days.

## Requirements

- Python 3.10+
- Pipenv

## Setup (Pipenv)

From the project root, install dependencies:

```bash
pipenv install
```

If `aiohttp` is not in your environment yet:

```bash
pipenv install aiohttp
```

## Run

Go to the `pw-5/console_utility` folder and run:

```bash
pipenv run python main.py <days> [currency1 currency2 ...]
```

Where:

- `<days>` is the number of days in the `1..10` range (without today).
- `[currency1 currency2 ...]` are optional extra currency codes (for example `PLN`, `GBP`).

## Command Examples

Base currencies only (`EUR`, `USD`) for 3 days:

```bash
pipenv run python main.py 3
```

Base + extra currencies (`PLN`, `GBP`) for 5 days:

```bash
pipenv run python main.py 5 PLN GBP
```

## Error Handling

- If days are outside `1..10`, the utility prints an error message.
- If a non-existent currency code is passed, the utility prints:
  `Error: Currency not found: <CODE>`.
- Network issues are reported as `Error: Connection error ...`.
