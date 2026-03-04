from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./mydb.db"

#Porque se creo así?
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}  # Requerido para SQLite en FastAPI
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session