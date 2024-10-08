from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from settings import settings, logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Base class for all models
Base = declarative_base()

# Engine and session for the database
engine = create_engine(settings.notes_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the DB session
def get_db():
    '''
    Description:
    This function provides a database session to be used for each request. 
    It ensures that the session is properly closed after the request.
    Yields:
    SessionLocal: The database session for querying and interacting with the database.
    Raises:
    Logs any unexpected database connection issues.
    '''
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


class Note(Base):
    '''
    The `Note` class represents a note in the database. 
    '''
    __tablename__ = "notes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    is_archive = Column(Boolean, default=False, index=True)
    is_trash = Column(Boolean, default=False, index=True)
    reminder = Column(DateTime, nullable=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    
    @property
    def to_dict(self):
        '''
        Description:
        Converts the Note instance to a dictionary.
        Returns:
        dict: A dictionary containing all attributes of the note.
        '''
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")


class Label(Base):
    '''
    The `Label` class represents a label in the database.
    '''
    __tablename__ = "labels"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)
    user_id = Column(BigInteger, nullable=False, index=True)