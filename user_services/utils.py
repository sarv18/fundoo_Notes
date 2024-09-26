from passlib.context import CryptContext

# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
