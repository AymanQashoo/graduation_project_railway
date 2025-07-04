from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter
from datetime import timezone
from pymongo.synchronous import collection

from database import get_db


SECRET_KEY = "123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5


router = APIRouter(prefix="/user", tags=["user"])

db= get_db()
collection=db["User"]


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")



from pydantic import BaseModel

# Pydantic model to validate the input
class UserInRegister(BaseModel):
    username: str
    password: str
    name: str

@router.post("/register")
async def register(user: UserInRegister):
    if collection.find_one({"username": user.username}):
        return {"message": "User already exists"}

    index_collection = db["index"]
    index_doc = index_collection.find_one_and_update(
        {},  
        {"$inc": {"current_user_number": 1}},
        return_document=True  
    )

    if not index_doc:
        raise HTTPException(status_code=500, detail="Index document not found")

    new_user_id = index_doc["current_user_number"]

    hashed_password = pwd_context.hash(user.password)
    collection.insert_one({
        "username": user.username,
        "hashed_password": hashed_password,
        "name": user.name,
        "userId": new_user_id
    })

    return {"message": "User registered successfully", "userId": new_user_id}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = collection.find_one({"username": form_data.username})
    
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        return {"message": "Invalid credentials"}
    access_token = create_access_token(data={"sub": user["name"], "userId": user["userId"]})

    return {"access_token": access_token, "token_type": "bearer", "name": user["name"] , "userId": user["userId"]}



@router.get("/getUser")
async def get_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        name: str = payload.get("sub")
        userId: int = payload.get("userId")
        if name is None or userId is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"name": name, "userId": userId}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# @router.get("/protected")
# async def protected_route(username: str = Depends(get_current_user)):
#     return {"message": f"Hello, {username}! This is a protected route."}

