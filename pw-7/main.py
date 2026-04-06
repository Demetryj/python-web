from conf.db import get_session

with get_session() as session:
    # Use `session` for database operations here.
    pass
