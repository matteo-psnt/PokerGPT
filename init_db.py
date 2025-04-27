from sqlalchemy import create_engine
from config.config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE
from db.models import Base

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}"

def init_db() -> None:
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
