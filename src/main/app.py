from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends
# from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
import socket
import uvicorn
import sys
from models import AppSettings
import logging
import database
from models import User

#-Logging configuration----------------------------
logger = logging.getLogger('API_Logger')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

#-Load Application settings-----------------------
settings = AppSettings()
MyUserDB = database.MongoDatabase(mongohost=settings.mongo_host, 
                                  mongoport=settings.mongo_port,
                                  mongouser=settings.mongo_user,
                                  mongopassword=settings.mongo_password, 
                                  database_name=settings.mongo_db_name, 
                                  user_coll_name=settings.mongo_usercoll_name)

# DB seeding for admin user
my_user = User(
    admin=True,
    age=30,
    first_name="admin",
    last_name="admin",
    gender="m",
    password="test",
    username="admin",
    avatar="https://gravatar.com/avatar/218f7cdc60ee506a63c30bd2441d8825?s=400&d=robohash&r=x"
)
MyUserDB.insert_one_user(my_user)

#-Initialization----------------------------------
app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Passwort-Hashing-Algorithmus
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT-Konfiguration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Benutzerdefinierter Benutzer
# fake_users_db = {
#     "myuser": {
#         "username": "myuser",
#         "hashed_password": pwd_context.hash("mypassword"),
#         "disabled": False,
#     }
# }

# OAuth2-Schema
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# SPA specific config
# class SPAStaticFiles(StaticFiles):
#     async def get_response(self, path: str, scope):
#         try:
#             return await super().get_response(path, scope)
#         except (HTTPException, StarletteHTTPException) as ex:
#             if ex.status_code == 404:
#                 return await super().get_response("index.html", scope)
#             else:
#                 raise ex

# Helper functions---------------------------------
# Erstellen des JWT-Tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Benutzerüberprüfungsfunktion
def authenticate_user(username: str, password: str):
    # Query the database for the user with the provided username
    users = MyUserDB.find_all_users()
    for user in users:
        print(user["username"])
        if user["username"] == username:
            hashed_password = user.get("password")
            if not hashed_password:
                return False
            if pwd_context.verify(password, hashed_password):
                return user
            else:
                return False
    return False


# Funktion zur Überprüfung des JWT-Tokens
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Remove the Bearer prefix from the token
    if token[:7] == "Bearer ":
        token = token[7:]

    # Try to decode and verify the token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return payload

#-API Area----------------------------------------

#- AUTH ------------------------------------------
# Route zum Erstellen des JWT-Tokens
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(form_data.username)
    print(form_data.password)
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid username or password"
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Geschützte Test Route
@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    logger.info("protected route called")
    current_user = await get_current_user(token)
    username = current_user["sub"]
    return {"message": f"Hello, {username}!"}

#- HOSTNAME ----------------------------------------------
# Get hostname
@app.get("/get")
async def render_root():
    logger.info("root route called")
    hostname = socket.gethostname()

    res_obj = {
        "message": f"Serving from {hostname}.",
        "status_code": 200
    }

    return res_obj

#- USER AREA ---------------------------------------------------

# Create User
@app.post("/api/v1/user")
async def create_user(user:User, token: str = Depends(oauth2_scheme)):
    logger.info("create_user route called")
    current_user = await get_current_user(token)
    username = current_user["sub"]
    # Query the database to retrieve the user details
    user_details = MyUserDB.get_user_by_username(username)
    
    # Check if the user has admin privileges
    if not user_details["admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin users can create users") 
    MyUserDB.insert_one_user(user)

    resObj = {
        "message": f"User {user.username} successfully created",
        "status_code": 200
    }

    return resObj

@app.get("/api/v1/users")
async def get_users(token: str = Depends(oauth2_scheme)):
    logger.info("get_users route called")
    current_user = await get_current_user(token)
    username = current_user["sub"]
    # Query the database to retrieve the user details
    user_details = MyUserDB.get_user_by_username(username)
    
    # Check if the user has admin privileges
    if not user_details["admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin users can list all users") 
    users = MyUserDB.find_all_users()

    resObj = {
        "users": users,
        "status_code": 200
    }

    return resObj

@app.get("/api/v1/user")
async def get_user(token: str = Depends(oauth2_scheme)):
    logger.info("get_user route called")
    current_user = await get_current_user(token)
    username = current_user["sub"]
    user = MyUserDB.get_user_by_username(username)

    resObj = {
        "users": user,
        "status_code": 200
    }

    return resObj

@app.delete('/api/v1/user/{userid}')
async def delete_user(userid:str, token: str = Depends(oauth2_scheme)):
    logger.info("delete_user route called")
    current_user = await get_current_user(token)
    username = current_user["sub"]
    # Query the database to retrieve the user details
    user_details = MyUserDB.get_user_by_username(username)
    
    # Check if the user has admin privileges
    if not user_details["admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin users can delete users") 
    MyUserDB.delete_user(userid)

    resObj = {
        "message": f"Userid {userid} deleted successfully.",
        "status_code": 200
    }

    return resObj

@app.put('/api/v1/user/{user_id}')
async def update_user(user_id: str, user:User, token: str = Depends(oauth2_scheme)):
    logger.info("update_user route called")
    current_user = await get_current_user(token)
    username = current_user["sub"]
    # Query the database to retrieve the user details
    user_details = MyUserDB.get_user_by_username(username)
    
    # Check if the user has admin privileges
    if not user_details["admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin users can update users") 

    MyUserDB.update_user(user_id, user)

    resObj = {
        "message": f"User {user_id} successfully updated.",
        "status_code": 200
    }

    return resObj

#-StaticFIles directory and api routes
# app.mount("/", SPAStaticFiles(directory="dist", html=True), name="dist")

#-Runner------------------------------------------
if __name__ == "__main__":
    if "dev".lower() in sys.argv:
        logger.info("FastAPI App started in DEV mode")
        uvicorn.run(app="__main__:app", host="0.0.0.0", port=settings.api_port, reload=True)
    else:
        logger.info("FastAPI App started")
        uvicorn.run(app="__main__:app", host="0.0.0.0", port=settings.api_port)
        logger.info("FastAPI app shut down")