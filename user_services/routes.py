import jwt
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from .models import User, get_db
from .schemas import UserRegistrationSchema, UserLoginSchema 
from .utils import hash_password, verify_password, create_token, create_tokens, send_verification_email
from settings import settings, logger
from tasks import send_mail
from sqlalchemy.exc import SQLAlchemyError


# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    '''
    Description: This is the handler function that gets called when a request is made to the root endpoint
    Parameters: None
    Return: A dictionary with a welcome message.
    '''
    return {"message": "Welcome to the Fundoo Notes API!"}

# Register a new user
@app.post("/register")
def register_user(request: Request, user: UserRegistrationSchema,  db: Session = Depends(get_db)):
    '''
    Discription: Registers a new user after validating the input, checking if the user exists, 
    hashing the password, and storing the user in the database.
    Parameters: 
    request: Request: Provides information about the HTTP request, which is used to generate the email verification link.
    user: UserRegistrationSchema: The request body is validated using the UserRegistrationSchema, 
    which ensures that all required fields are correctly formatted.
    db: Session = Depends(get_db): Uses dependency injection to pass the current database session to the function.
    Return: Returns a JSON response with a success message and the registered user's data 
    (using the to_dict() method of the User model).
    '''
    try:
        # Check if the user already exists by email
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.error(f"Attempt to register an existing email: {user.email}")
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

        # Generate the access token
        access_token = create_token({"sub": db_user.email}, "access")

        # Generate verification link
        verify_link = request.url_for('verify_registered_user', token=access_token)

        # Send verification email using Celery task
        send_mail.delay(db_user.email, str(verify_link))

        logger.info(f"User registered: {user.email}")
        return {
            "message": "User registered successfully",
            "status": "success",
            "data": db_user.to_dict,
            "access_token": access_token
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during user registration: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
    try:
        # Check if the user exists in the database by email
        db_user = db.query(User).filter(User.email == user.email).first()
        
        if not db_user or not verify_password(user.password, db_user.password):
            logger.warning(f"Invalid login attempt for email: {user.email}")
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Generate both JWT tokens
        access_token, refresh_token = create_tokens({"sub": db_user.email, "user_id": db_user.id})

        logger.info(f"User logged in: {user.email}")
        return {
            "message": "Login successful",
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "data": db_user.to_dict
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error during login: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/verify/{token}")
def verify_registered_user(token: str, db: Session = Depends(get_db)):
    '''
    Description: Verifies a user's email by decoding the token and marking the user as verified.
    Parameters: 
    token: The verification token sent to the user.
    db: Dependency to interact with the database.
    Return: Success message if the email is successfully verified.
    '''
    try:
        # Decode the token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")

        if email is None:
            logger.error("Invalid token: email not found in payload")
            raise HTTPException(status_code=400, detail="Invalid token")

        # Fetch the user from the database
        user = db.query(User).filter(User.email == email).first()

        if not user:
            logger.error(f"User not found: {email}")
            raise HTTPException(status_code=404, detail="User not found")

        # Mark user as verified
        if user.is_verified:
            return {"message": "User is already verified"}
    
        # Verify the user
        user.is_verified = True
        db.commit()

        logger.info(f"User verified: {email}")
        return {"message": "Email verified successfully!"}

    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        raise HTTPException(status_code=400, detail="Token has expired")

    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        raise HTTPException(status_code=400, detail="Invalid token")

    except SQLAlchemyError as e:
        logger.error(f"Database error during verification: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/user/{token}",status_code= 200, include_in_schema= False)
def auth_user(token: str, db: Session = Depends(get_db)):
    '''
    Description: Decodes the JWT token and fetches the authenticated user's data from the database.
    Parameters: 
    token: JWT token containing the user ID.
    db: Database session.
    Return: A JSON response with the user's data if the token is valid.
    '''
    try:
        # Decode the JWT token to get payload
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        # print(payload)
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            logger.warning("Invalid user ID in token")
            raise HTTPException(status_code=401, detail="Invalid User ID")
        
        # Fetch user details from the database based on user_id from token
        db_user = db.query(User).filter(User.id == user_id).first()
        
        if not db_user:
            logger.warning(f"User not found for ID: {user_id}")
            raise HTTPException(status_code=404, detail= "User not found")
        
        logger.info(f"User authenticated: {db_user.email}")
        # Return user details in JSON format
        return {
            "message": "Authorizaton successful",
            "status": "success",
            "data": db_user.to_dict
        }
        
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")

    except SQLAlchemyError as e:
        logger.error(f"Database error during user authentication: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during user authentication: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")