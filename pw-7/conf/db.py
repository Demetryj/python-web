import configparser
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

BASE_PATH = Path(__file__).resolve().parent

# Load config from one level above the conf directory: ../config.ini
file_config = BASE_PATH.parent.joinpath("config.ini")
config = configparser.ConfigParser()

# If the file cannot be read, stop early with a clear error.
if not config.read(file_config):
    raise FileNotFoundError(f"Config file not found or unreadable: {file_config}")

# Expect a dedicated section with development database settings.
if not config.has_section("DEV_DB"):
    raise ValueError("Missing [DEV_DB] section in config.ini")

# Validate the required connection parameters.
required_options = ("USER", "PASSWORD", "DOMAIN", "PORT", "DB_NAME")
missing_options = [opt for opt in required_options if not config.has_option("DEV_DB", opt)]
if missing_options:
    missing = ", ".join(missing_options)
    raise ValueError(f"Missing option(s) in [DEV_DB]: {missing}")

user = config.get("DEV_DB", "USER")
password = config.get("DEV_DB", "PASSWORD")
domain = config.get("DEV_DB", "DOMAIN")
port = config.getint("DEV_DB", "PORT")
db = config.get("DEV_DB", "DB_NAME")

# URI = f"postgresql://{user}:{password}@{domain}:{port}/{db}"
# Build URI via SQLAlchemy URL to safely handle special characters (like @).
URI = URL.create(
    drivername="postgresql",
    username=user,
    password=password,
    host=domain,
    port=port,
    database=db,
).render_as_string(hide_password=False)

# Create a single shared engine; echo is disabled to avoid noisy SQL logs.
engine = create_engine(URI, echo=False, pool_size=5, max_overflow=0)
# Session factory: each operation/request should use its own short-lived session.
DBsession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session():
    # Context manager guarantees commit/rollback/close in the correct order.
    session = DBsession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
