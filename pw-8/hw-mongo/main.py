import redis
from redis_lru import RedisLRU
from mongoengine import disconnect

from connection import init_mongoDB
from models import Author, Quote

# connect to Redis DB
client = redis.StrictRedis(host="localhost", port=6379, password=None)
cache = RedisLRU(client)

bot_command_list = """
Hello!\n
Commands:
name:<author_name> - find and return a list of all citations by an author
tag:<tag_name> - find and return a list of quotes for a tag
tags:<tag_name>,<tag_name> - find and return a list of quotes where these tags are present
!!!Note: no spaces between tags and <tag_name> / name and <author_name>
exit - bot shutdown
"""


def parse_input(user_input: str):
    """
    Parse raw CLI input into a normalized command and its value.

    Expected input formats:
    - "exit"
    - "name:<author_name>"
    - "tag:<tag_name>"
    - "tags:<tag1>,<tag2>"

    Behavior:
    - Removes leading/trailing spaces from the full input.
    - Returns ("_", "") for empty input or unsupported format.
    - Returns ("exit", "") when user enters exactly "exit" (case-insensitive).
    - For command inputs with ":", splits only by the first ":" to preserve
      the rest of the value as-is.
    - Normalizes command to lowercase and strips spaces around both command
      and value.

    Args:
        user_input: Raw string entered by the user in terminal.

    Returns:
        tuple[str, str]:
        - command name (or "_" for invalid/unknown shape)
        - command value (empty string when absent)
    """
    row = user_input.strip()

    if not row:
        return "_", ""

    if row.lower() == "exit":
        return "exit", ""

    if ":" not in row:
        return "_", ""

    command, value = row.split(":", 1)
    return command.strip().lower(), value.strip()


@cache
def find_quotes_by_author_name(author_name: str) -> list[str]:
    """
    Find quote texts for authors matching the given name pattern.

    This function supports shortened input (for example, "st") because
    it uses a case-insensitive regular expression filter against Author.fullname.

    Workflow:
    - Trim spaces from the provided author name.
    - If value is empty, return an empty list immediately.
    - Query all authors whose fullname matches the regex pattern.
    - If no authors are found, return an empty list.
    - Query quotes where quote.author is in the matched authors.
    - Return only quote text values as list[str].

    Note:
    - Because regex is used directly, special regex symbols in input may
      affect matching behavior.

    Args:
        author_name: Full or shortened author name from `name:<value>`.

    Returns:
        list[str]: Quote texts for all matched authors, or empty list.
    """
    author_name = author_name.strip()
    if not author_name:
        return []

    authors = Author.objects(fullname__iregex=author_name)
    if not authors:
        return []

    quotes = Quote.objects(author__in=authors)
    return [q.quote for q in quotes]


@cache
def find_quotes_by_tag(tag: str) -> list[str]:
    """
    Find quote texts by a single tag (supports partial tag input).

    Workflow:
    - Trim spaces from incoming tag value.
    - Return empty list for empty input to avoid broad "match-all" query.
    - Query quotes by case-insensitive regex against elements in tags list.
    - Return only quote text values as list[str].

    Args:
        tag: Tag value from `tag:<value>`.

    Returns:
        list[str]: Quote texts matching the tag pattern, or empty list.
    """
    if not tag.strip():
        return []
    quotes = Quote.objects(tags__iregex=tag)
    return [q.quote for q in quotes]


def find_quotes_by_tags(tags: list[str]) -> list[str]:
    """
    Find quote texts where at least one of provided tags is present.

    Intended for command `tags:<tag1>,<tag2>,...`.

    Workflow:
    - Strip spaces around each tag.
    - Drop empty tag items (for example, from extra commas).
    - If resulting tag list is empty, return empty list.
    - Query quotes with `tags__in`, which means logical OR semantics:
      quote is returned when any element in quote.tags matches any tag
      from the provided list.
    - Return only quote text values.

    Args:
        tags: Raw list of tags (usually result of `value.split(",")`).

    Returns:
        list[str]: Quote texts matching any of the provided tags.
    """
    clean_tags = [t.strip() for t in tags if t.strip()]
    if not clean_tags:
        return []
    return [q.quote for q in Quote.objects(tags__in=clean_tags)]


def main():
    """
    Run interactive command-line bot for searching quotes in MongoDB.

    Responsibilities:
    - Print command help message.
    - Initialize MongoDB connection once at startup.
    - Read user input in an infinite loop.
    - Route parsed commands to corresponding query functions.
    - Print query results or "Unknown command" for unsupported input.
    - Handle graceful shutdown for `exit`.
    - Always disconnect from MongoDB in `finally`, even on errors.

    Supported commands:
    - `name:<author_name>`: find quotes by author name/pattern
    - `tag:<tag_name>`: find quotes by one tag/pattern
    - `tags:<tag1>,<tag2>`: find quotes by multiple tags (OR logic)
    - `exit`: stop the bot
    """
    print(bot_command_list)
    init_mongoDB()

    try:
        while True:
            user_input = input(">>> Enter a command: ")
            command, value = parse_input(user_input)

            match command:
                case "exit":
                    print("Goodbye!")
                    break
                case "name":
                    print(find_quotes_by_author_name(value))
                case "tag":
                    print(find_quotes_by_tag(value))
                case "tags":
                    print(find_quotes_by_tags(value.split(",")))
                case _:
                    print("Unknown command")
    finally:
        disconnect(alias="default")


if __name__ == "__main__":
    main()
