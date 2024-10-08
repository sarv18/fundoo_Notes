from pydantic import BaseModel
from datetime import datetime

# Schema for creating new note
class CreateNote(BaseModel):
    """
    This schema is used for creating a new note. It defines the fields required 
    for creating a note and provides default values where applicable.
    """
    title: str
    description: str
    color: str
    is_archive: bool= False
    is_trash: bool= False
    reminder: datetime | None= None
    
# Schema for creating new label
class CreateLabel(BaseModel):
    """
    This schema is used for creating a new label. It defines the fields required 
    for label creation and ensures proper data validation.
    """
    name: str
    color: str
