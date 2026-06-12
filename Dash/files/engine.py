import sqlalchemy as sql
from urllib.parse import quote_plus
from pathlib import Path
from dotenv import load_dotenv
from db_config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE

load_dotenv()

def get_engine():
    password_encoded = quote_plus(DB_PASSWORD)

    engine  = sql.create_engine(
        f"postgresql+psycopg2://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}",
        connect_args={'options':'-c statement_timeout=300000'}
    )
    return engine

def load_query(qry_name):
    base_path = Path(__file__).parent.parent
    path = base_path / 'sql' / qry_name
    with open(path, 'r', encoding='utf-8') as file:
        
        return file.read()

def get_engine_heavy():
    password_encoded = quote_plus(DB_PASSWORD)

    engine  = sql.create_engine(
        f"postgresql+psycopg2://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}",
        connect_args={'options':'-c statement_timeout=600000'}
    )
    return engine


def close_engine():
    pass


