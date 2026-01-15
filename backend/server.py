import os
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select



app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Render provides 'postgres://' but SQLAlchemy needs 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    connect_args = {}
    engine = create_engine(database_url, connect_args=connect_args)
else:
    # Fallback to local SQLite
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str

class ShotData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    club: str | None = Field(default=None, index=True)
    direction: str | None = Field(default=None, index=True)
    directionYards: int = Field(default=0, ge=0)
    distance: str | None = Field(default=None)
    distanceYards: int = Field(default=0, ge=0)
    strikeType1: str | None = Field(
        default=None,
        description="Toe or Heel strike"
    )
    strikeType2: str | None = Field(
        default=None,
        description="Thin or Chunky strike"
    )


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "CaddyBot API is running"}

@app.post("/shot")
async def save_shot(shot: ShotData):
    print(f"Received shot data: {shot}")
    # Here you would typically save to a database
    return {"message": "Shot recorded successfully", "data": shot}

@app.post("/shots/")
def create_shot(shot: ShotData, session: SessionDep) -> ShotData:
    session.add(shot)
    session.commit()
    session.refresh(shot)
    return shot

@app.get("/shots/")
def read_shots(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[ShotData]:
    shots = session.exec(select(ShotData).offset(offset).limit(limit)).all()
    return shots


