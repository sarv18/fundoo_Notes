from pydantic import BaseModel, EmailStr, field_validator
import re
from settings import logger

# Schema for creating a new user
class UserRegistrationSchema(BaseModel):
    '''
    Defines a model for user registration. 
    This model inherits from BaseModel and fields are type-annotated.
    '''
    email: EmailStr
    password: str
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    def validate_name(cls, value):
        '''
        Description: This method validates both the first_name and last_name fields.
        Parameters: 
        cls: The class the method is attached to.
        value: The value of the field (either first name or last name) that will be validated.
        Return: Returns the validated value if it passes the check.
        '''
        try:
            if len(value) < 3:
                raise ValueError("Name must contain at least 3 characters")
            return value
        except ValueError as e:
            logger.error(f"Name validation error: {e}")
            raise
        
    @field_validator("email")
    def validate_email(cls, value):
        '''
        Description: Validates the email format.
        Parameters:
        cls: The class the method is attached to.
        value: The email field being validated.
        Return: The validated email or raises a ValueError if the format is incorrect.
        '''
        try:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
                raise ValueError("Invalid email format")
            return value
        except ValueError as e:
            logger.error(f"Email validation error: {e}")
            raise

    @field_validator("password")
    def validate_password(cls, value):
        '''
        Description: Validates the password strength by ensuring it has at least 8 characters 
        and contains at least one special character.
        Parameters:
        cls: The class the method is attached to.
        value: The password field being validated.
        Return: The validated password or raises a ValueError if it fails the checks.
        '''
        try:
            if len(value) < 8 or not re.search(r'\W', value):
                raise ValueError("Password must contain at least 8 characters and 1 special character")
            return value
        except ValueError as e:
            logger.error(f"Password validation error: {e}")
            raise


# Schema for user login
class UserLoginSchema(BaseModel):
    '''
    This class is used for validating the login request, 
    ensuring that an email and password are provided.
    '''
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        '''
        Description: Ensures the password is not empty.
        Parameters:
        cls: The class the method is attached to.
        value: The password field being validated.
        Return: The validated password or raises a ValueError if it's empty.
        '''
        try:
            if len(value) == 0:
                raise ValueError("Password cannot be empty")
            return value
        except ValueError as e:
            logger.error(f"Password validation error during login: {e}")
            raise

