import requests as http
from fastapi import Request, HTTPException
import redis
import json

def auth_user(request: Request):
    token = request.headers.get("Authorization")
    response = http.get(url= f"http://127.0.0.1:8000/user/{token}")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail= "Invalid User")
    
    user_data = response.json()["data"]
    request.state.user = user_data
    
    
class RedisUtils():
    # Initialize Redis connection
    r = redis.Redis(host= "localhost", port=6379, decode_responses= True, db= 0)
    
    @classmethod
    def save(self, key, field, value):
        '''
        Save data in Redis (can handle both create and update).
        Key is the Redis hash key, and the field is the hash field.
        The value should be passed as a dictionary.
        '''
        self.r.hset(key, field, json.dumps(value, default= str))
        return True
    
    @classmethod
    def get(self, key):
        '''
        Retrieve data from Redis. If field is provided, use hget, else fetch all fields with hgetall.
        '''
        data = self.r.hgetall(key)
        return [json.loads(x) for x in data.values()]
        
    @classmethod
    def delete(self, key, field=None):
        '''
        Delete data from Redis.
        If field is provided, only that field will be deleted from the hash.
        If field is None, the entire key will be deleted.
        '''
        if field:
            self.r.hdel(key, field)
        return True