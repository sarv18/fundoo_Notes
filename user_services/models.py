from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from settings import settings, logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException


Base = declarative_base()

# Create engine and session
engine = create_engine(settings.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the DB session
def get_db():
    """
    Dependency function to get a new database session.
    This function provides a database session (`db`) that can be used in request handlers.
    The session is opened at the beginning and properly closed after the request completes.
    Yields:
    db (SessionLocal): A new SQLAlchemy session connected to the database.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        raise HTTPException(status_code=500, detail="Internal database error")
    finally:
        try:
            db.close()
            logger.info("Database session closed.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to close the database session: {e}")

class User(Base):
    """
    Represents a `User` table in the database.
    """
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


    @property
    def to_dict(self):
        """
        Converts the `User` object to a dictionary format, excluding the password field.
        Returns:
        dict: A dictionary containing all the User attributes, except for the password.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")

