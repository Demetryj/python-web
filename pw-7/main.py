from sqlalchemy.orm import Session

from conf.db import get_session
from repository import my_select as queries


def run_query(n: int, session: Session, **kwargs):
    """Dynamically finds and runs select_N(session) from repository.my_select."""
    fn = getattr(queries, f"select_{n}", None)
    if fn is None:
        raise ValueError(f"Query select_{n} not found")
    return fn(session, **kwargs)


def main(session: Session, **kwargs):
    result = run_query(n=12, session=session, **kwargs)

    if result:
        if isinstance(result, list):
            for r in result:
                print(r)
        else:
            print(str(result))
    else:
        print("No data")


if __name__ == "__main__":

    with get_session() as session:
        main(session, group="Pb-75", discipline = "majority various speak")
