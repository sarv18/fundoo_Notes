from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from settings import settings
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
    return pwd_context.hash(password)

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
    return pwd_context.verify(plain_password, hashed_password)

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
    if token_type == "access":
        expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes))
    elif token_type == "refresh":
        expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes))
    else:
        raise ValueError("Invalid token type. Must be 'access' or 'refresh'.")

    return jwt.encode({**data, "exp": expiration}, settings.secret_key, algorithm=settings.algorithm)

# To generate both tokens
def create_tokens(data: dict):
    """
    Generates both access and refresh tokens.
    """
    access_token = create_token(data, "access")
    refresh_token = create_token(data, "refresh")
    return access_token, refresh_token
 
async def send_verification_email(email: str, verify_link: str):
    """
    Description:
    Sends a verification email to the user.
    Parameters:
    email : The email address of the user to send the verification link to.
    verify_link : The verification link to be included in the email.
    """
    # Send verification email
    message = MessageSchema(
        subject= "FundooNotes - Verify your email",
        recipients= [email],
        body= f"Click on the link to verify your email: {verify_link}",
        subtype= "html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)