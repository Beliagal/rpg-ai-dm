import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Inicializar las variables de entorno correctamente
load_dotenv()

# Configuración de SQLite local
DATABASE_URL = "sqlite:///./rpg_database.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Uso de sqlalchemy.orm.declarative_base() estándar en 2.x
Base = declarative_base()

def get_db():
    """Generador de sesiones de base de datos para la inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()