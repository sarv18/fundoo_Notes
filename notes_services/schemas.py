from pydantic import BaseModel
from datetime import datetime
from typing import List

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
    reminder: datetime = datetime.now()
    
# Schema for creating new label
class CreateLabel(BaseModel):
    """
    This schema is used for creating a new label. It defines the fields required 
    for label creation and ensures proper data validation.
    """
    name: str
    color: str

# Pydantic model for the request body
class AddNoteLabels(BaseModel):
    """
    Pydantic model for adding labels to notes.
    """
    label_ids: List[int]
    
    
class AddCollaborators(BaseModel):
    
    note_id: int
    user_ids: List[int]
    access: str  # 'readonly' or 'readwrite'

class RemoveCollaborators(BaseModel):
    
    note_id: int
    user_ids: List[int]
