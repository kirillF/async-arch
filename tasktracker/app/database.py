from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import asyncio
import os

# Get the database connection configuration from environment variables
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")
db_name = os.getenv("POSTGRES_DB")

# Create the database connection URL
db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"Database URL: {db_url}")


# Create the SQLAlchemy engine
engine = create_async_engine(db_url)

# Create a session factory
AsyncSession = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Create the database tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Run the create_tables function
asyncio.create_task(create_tables())
