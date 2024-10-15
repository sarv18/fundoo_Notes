from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Table, ForeignKey
from settings import settings, logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import JSON

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


# Association table between Note and Label
note_label_association = Table(
    'note_label_association',
    Base.metadata,
    Column('note_id', BigInteger, ForeignKey('notes.id', ondelete='CASCADE'), primary_key=True),
    Column('label_id', BigInteger, ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True)
)


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
    
    # Column for storing collaborators (as a JSON object)
    collaborators = Column(JSON, default={})
    
    # Establish many-to-many relationship with labels
    labels = relationship("Label", secondary=note_label_association, back_populates="notes")
    
    @property
    def to_dict(self):
        '''
        Description:
        Converts the Note instance to a dictionary.
        Returns:
        dict: A dictionary containing all attributes of the note.
        '''
        try:
            object_data = {col.name: getattr(self, col.name) for col in self.__table__.columns}
            labels = []
            if self.labels:
                labels = [x.to_dict for x in self.labels]
            object_data.update(labels = labels)
            return object_data

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
    
    # Establish many-to-many relationship with notes
    notes = relationship("Note", secondary=note_label_association, back_populates="labels")
    
    @property
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
    
