from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import User, get_db
from .schemas import UserRegistrationSchema, UserLoginSchema
from .utils import hash_password, verify_password

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    '''
    Discription: This is the handler function that gets called when a request is made to the root endpoint
    Parameters: None
    Return: A dictionary with a welcome message.
    '''
    return {"message": "Welcome to the Fundoo Notes API!"}

# Register a new user
@app.post("/register")
def register_user(user: UserRegistrationSchema, db: Session = Depends(get_db)):
    '''
    Discription: Registers a new user after validating the input, checking if the user exists, 
    hashing the password, and storing the user in the database.
    Parameters: 
    user: UserRegistrationSchema: The request body is validated using the UserRegistrationSchema, 
    which ensures that all required fields are correctly formatted.
    db: Session = Depends(get_db): Uses dependency injection to pass the current database session to the function.
    Return: Returns a JSON response with a success message and the registered user's data 
    (using the to_dict() method of the User model).
    '''
    # Check if the user already exists by email
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the user's password
    hashed_password = hash_password(user.password)

    # Create a new User object
    db_user = User(
        email=user.email, 
        password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Add the user to the database and commit the transaction
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "message": "User registered successfully",
        "status": "success",
        "data": db_user.to_dict
    }

# User login
@app.post("/login")
def login_user(user: UserLoginSchema, db: Session = Depends(get_db)):
    '''
    Discription:  Logs in a user by verifying their email and password against the database, 
    returning a success message if they match.
    Parameters: 
    user: UserLoginSchema: The request body is validated using the UserLoginSchema (email and password).
    db: Session = Depends(get_db): Dependency injection is used to get a database session via the get_db function.
    Return: If the email and password match, a success message is returned, along with the logged-in user's data.
    '''
    # Check if the user exists in the database by email
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {
        "message": "Login successful",
        "status": "success",
        "data": db_user.to_dict
    }
