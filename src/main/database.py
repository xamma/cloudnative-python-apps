import pymongo
import models
from bson import ObjectId
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MongoDatabase():
    """
    Initializing MongoDB and conn.

    :Init Vars:
    mongohost = str
    mongoport = str

    """
    def __init__(self, mongohost:str, mongouser:str, mongopassword:str, mongoport:int, database_name:str, user_coll_name:str) -> None:
        self.monghost = mongohost
        self.mongoport =  mongoport
        self.mongouser = mongouser
        self.mongopassword = mongopassword
        self.mydb = database_name
        self.usercoll = user_coll_name
        self.myclient = None
        self.setup_connection()

    def setup_connection(self):
        uri = f"mongodb://{self.mongouser}:{self.mongopassword}@{self.monghost}:{self.mongoport}/"
        self.myclient = pymongo.MongoClient(uri)
        self.mydb = self.myclient[self.mydb]
        self.usercoll = self.mydb[self.usercoll]

    # USER CRUD
    def insert_one_user(self, item: models.User):
        # Check if the username already exists in the database
        existing_user = self.usercoll.find_one({"username": item.username})
        if existing_user:
            print("Username already exists in the database")
            return False
        # Hash the password if it exists
        # print(item)
        if item.password:
            hashed_password = pwd_context.hash(item.password)
            item = item.copy(update={"password": hashed_password})

        if item.avatar:
            avatar_url = "https://gravatar.com/avatar/218f7cdc60ee506a63c30bd2441d8825?s=400&d=robohash&r=x"
            item = item.copy(update={"avatar": avatar_url})

        # Insert the user into the database
        self.usercoll.insert_one(item.dict())

    def find_all_users(self) -> list:
        """
        Gets all users from the database
        """
        cursor = self.usercoll.find({})
        docuements = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            docuements.append(doc)
        return docuements
    
    def get_user_by_username(self, username:str):
        """
        Retrieves user information based on the username.
        """
        user = self.usercoll.find_one({"username": username})
        user["_id"] = str(user["_id"])

        return user

    
    def delete_user(self, id:str):
        """
        Deletes a user from the database
        """
        self.usercoll.delete_one({'_id': ObjectId(id)})

    def update_user(self, user_id: str, user: models.User):
        """
        Updates a user in the database
        """
        update_fields = {}

        if user.first_name is not None:
            update_fields["first_name"] = user.first_name
        if user.avatar is not None:
            update_fields["avatar"] = user.avatar
        if user.username is not None:
            update_fields["username"] = user.username
        if user.last_name is not None:
            update_fields["last_name"] = user.last_name
        if user.age is not None:
            update_fields["age"] = user.age
        if user.gender is not None:
            update_fields["gender"] = user.gender
        if user.admin is not None:
            update_fields["admin"] = user.admin
        if user.achievements is not None:
            update_fields["achievements"] = user.achievements
        if user.password is not None:
            hashed_password = pwd_context.hash(user.password)
            update_fields["password"] = hashed_password

        query = {"_id": ObjectId(user_id)}
        new_values = {"$set": update_fields}
        self.usercoll.update_one(query, new_values)
