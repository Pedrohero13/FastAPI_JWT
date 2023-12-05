from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from sql_app import util_user
from . import crud, models, schemas
from .database import SessionLocal, engine
from typing import Annotated

from datetime import timedelta

from fastapi.security import  OAuth2PasswordRequestForm



ACCESS_TOKEN_EXPIRE_MINUTES = 60
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/token", response_model=schemas.Token, )
async def login_for_access_token(
    form_data: schemas.userLogin,
    db: Session = Depends(get_db)
):
    user = util_user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = util_user.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)]
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.post("/users/", response_model=schemas.User)
async def create_user(current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)],
                      user: schemas.UserCreate, 
                      db: Session = Depends(get_db) ):
    
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
async def read_users(current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)],
               skip: int = 0, 
               limit: int = 100, 
               db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)],
              user_id: int, 
              db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
async def create_item_for_user(
    current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)],
    user_id: int, 
    item: schemas.ItemCreate, 
    db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=list[schemas.Item])
def read_items(current_user: Annotated[schemas.User, Depends(util_user.get_current_active_user)],
               skip: int = 0, 
               limit: int = 100, 
               db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items