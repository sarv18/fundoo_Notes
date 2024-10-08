import requests as http
from fastapi import Request, HTTPException
import redis
import json
from settings import settings, logger

def auth_user(request: Request):
    """
    Description:
    Authenticate the user by verifying the Authorization token in the request headers.
    Parameters:
    request: The FastAPI request object containing the headers.
    Returns:
    None: Sets the `request.state.user` with user data if authentication is successful.
    """
    try:
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Authorization token missing")
        
        response = http.get(url=f"{settings.endpoint}{token}")
        
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail="Invalid User")
        
        user_data = response.json().get("data")
        if not user_data:
            raise HTTPException(status_code=401, detail="User data missing in response")

        request.state.user = user_data
        logger.info("User authenticated successfully.")
        
    except Exception as e:
        logger.error(f"Error during user authentication: {str(e)}")
        raise HTTPException(status_code=500, detail="User authentication failed")
    
    
class RedisUtils():
    # Initialize Redis connection
    r = redis.Redis(host= "localhost", port=6379, decode_responses= True, db= 0)
    
    @classmethod
    def save(self, key, field, value):
        """
        Description:
        Saves data in Redis (either creating new data or updating existing data).
        The data is stored as a hash in Redis where 'key' is the Redis hash key, and 'field' is the hash field.
        Parameters:
        key (str): The Redis key that identifies the hash.
        field (str): The field within the hash to store the value.
        value (dict): The dictionary data to be stored as the field's value.
        Return:
        bool: Returns True if the operation was successful.
        """
        try:
            self.r.hset(key, field, json.dumps(value, default=str))
            logger.info(f"Data saved in Redis key: {key}, field: {field}")
            return True
        except Exception as e:
            logger.error(f"Error saving data in Redis key: {key}, field: {field}. Error: {str(e)}")
            raise
    
    @classmethod
    def get(self, key):
        """
        Description:
        Retrieves data from Redis. If multiple fields are stored, all are fetched using `hgetall`.
        Parameters:
        key (str): The Redis key that identifies the hash.
        Returns:
        dict: A dictionary of values stored in the Redis hash (as dictionaries).
        """
        try:
            data = self.r.hgetall(key)
            if not data:
                logger.warning(f"No data found in Redis for key: {key}")
                return []
            logger.info(f"Data retrieved from Redis key: {key}")
            return [json.loads(x) for x in data.values()]
        except Exception as e:
            logger.error(f"Error retrieving data from Redis key: {key}. Error: {str(e)}")
            raise
        
    @classmethod
    def delete(self, key, field=None):
        """
        Description:
        Deletes data from Redis. If a field is provided, only that field is deleted from the hash. 
        If no field is provided, the entire Redis key is deleted.
        Parameters:
        key (str): The Redis key that identifies the hash.
        field (str, optional): The specific field to delete within the hash. Defaults to None.
        Returns:
        bool: Returns True if the operation was successful.
        """
        try:
            if field:
                self.r.hdel(key, field)
                logger.info(f"Field '{field}' deleted from Redis key: {key}")
            else:
                self.r.delete(key)
                logger.info(f"Redis key '{key}' deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting data from Redis key: {key}, field: {field}. Error: {str(e)}")
            raise