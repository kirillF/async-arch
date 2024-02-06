from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os


# Get the database connection configuration from environment variables
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")
db_name = os.getenv("POSTGRES_DB")

# Create the database connection URL
db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the SQLAlchemy engine
engine = create_async_engine(db_url)

# Create a session factory
AsyncSession = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the FastAPI app
app = FastAPI()

# Define your routes and endpoints here


# Example route
@app.get("/")
def read_root():
    return {"Hello": "World"}


# Example route that uses the database connection
@app.get("/users")
def get_users():
    # Open a new session
    db = SessionLocal()

    # Perform database operations here

    # Close the session
    db.close()

    return {"message": "Users retrieved successfully"}
