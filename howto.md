# How-to
## Usage
The example app found in this repository is an RESTApi Backend for CRUD operations on a User.  
The model is defined via pydantic and the ENV vars are set via pydantic-settings.  
The user object is stored in MongoDB, a NoSQL database.  

## Create the mongo instance
If you want to try the setup on your localhost create a mongodb via docker:
```
docker run -dp 27017:27017 -v mongodata:/data/db mongo
```

## Get started
Run the code
```
python -m venv venv
./venv/bin/activate.sh
pip install -r /src/requirements.txt
python /src/main/app.py
```

Build container
```
docker build -t myimage .
docker run -dp 8888:8000 -e SOMEKEY=SOMEVAL myimage
```

## Features
- Connection and initialization of MongoDB
- OAuth2 to protect the API routes
- CRUD operations for Users
- Dockerfile
- k8s-templates
- Models and validation via pydantic