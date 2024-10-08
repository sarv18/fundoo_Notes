from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from settings import settings, logger
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME = settings.mail_username,
    MAIL_PASSWORD = settings.mail_password,
    MAIL_FROM = settings.mail_from,
    MAIL_PORT = settings.mail_port,
    MAIL_SERVER = settings.mail_server,  
    MAIL_FROM_NAME = settings.mail_from_name,
    MAIL_STARTTLS = settings.mail_starttls,
    MAIL_SSL_TLS = settings.mail_ssl_tls,
    USE_CREDENTIALS = settings.use_credentials
)

# Utility function to hash a password
def hash_password(password: str) -> str:
    '''
    Discription: Takes a plain text password and returns a hashed version of it using bcrypt.
    Parameters: 
    password: str: A string representing the plain text password that needs to be hashed.
    Return: 
    str: Returns the hashed version of the password as a string.
    '''
    try:
        hashed_password = pwd_context.hash(password)
        logger.info("Password hashed successfully.")
        return hashed_password
    except Exception as e:
        logger.error(f"Error while hashing password: {str(e)}")
        raise ValueError("Password hashing failed.")


# Utility function to verify hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''
    Discription: Takes a plain text password and a hashed password and checks if 
    they are equivalent by hashing the plain text and comparing the result.
    Parameters: 
    plain_password: str: The plain text password input by the user.
    hashed_password: str: The hashed password that was stored (e.g., during user registration).
    Return: 
    bool: Returns True if the plain text password matches the hashed password, otherwise False.
    '''
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.info("Password verification successful.")
        return is_valid
    except Exception as e:
        logger.error(f"Error while verifying password: {str(e)}")
        return False


# Unified Token Generation Function
def create_token(data: dict, token_type: str, exp= None):
    """
    Creates a token (either access or refresh) based on the token_type parameter.
    Parameters:
    data (dict): Data to encode into the token.
    token_type (str): The type of token to create, either 'access' or 'refresh'.
    exp (datetime, optional): Optional expiration time. If not provided, defaults are used.
    Returns:
    str: The encoded JWT token.
    """
    try:
        if token_type == "access":
            expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes))
        elif token_type == "refresh":
            expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes))
        else:
            raise ValueError("Invalid token type. Must be 'access' or 'refresh'.")

        token = jwt.encode({**data, "exp": expiration}, settings.secret_key, algorithm=settings.algorithm)
        logger.info(f"{token_type.capitalize()} token created successfully.")
        return token

    except Exception as e:
        logger.error(f"Error while creating {token_type} token: {str(e)}")
        raise
  
    
# To generate both tokens
def create_tokens(data: dict):
    """
    Description:
    Generates both access and refresh tokens for a given user.
    Parameters:
    data : Data to encode into the tokens.
    Returns:
    tuple: A tuple containing the access token and refresh token.
    """
    try:
        access_token = create_token(data, "access")
        refresh_token = create_token(data, "refresh")
        logger.info("Access and refresh tokens created successfully.")
        return access_token, refresh_token
    except Exception as e:
        logger.error(f"Error while generating tokens: {str(e)}")
        raise
    
 
# Function to send verification email asynchronously
async def send_verification_email(email: str, verify_link: str):
    """
    Description:
    Sends a verification email to the user.
    Parameters:
    email : The email address of the user to send the verification link to.
    verify_link : The verification link to be included in the email.
    Return: None
    """
    try:
        # Create the email message
        message = MessageSchema(
            subject="FundooNotes - Verify your email",
            recipients=[email],
            body=f"Click on the link to verify your email: {verify_link}",
            subtype="html"
        )

        # Initialize FastMail instance and send email
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Verification email sent to {email}.")

    except Exception as e:
        logger.error(f"Error while sending verification email to {email}: {str(e)}")
        raise ValueError("Failed to send verification email.")
    