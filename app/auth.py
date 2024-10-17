from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(db: Session, username: str, password: str):
    korisnik = crud.get_korisnik(db, username)
    if korisnik and crud.hash_password(password) == korisnik.hashed_password:
        return korisnik
    return None

def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if user_id is None:
        return RedirectResponse(url="/login")
    return user_id