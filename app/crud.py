from sqlalchemy.orm import Session
from app import models
from app import schemas
from app.models import Favorit, Korisnik
from app.schemas import KorisnikCreate
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_korisnik_by_email(db: Session, email: str):
    return db.query(Korisnik).filter(Korisnik.email == email).first()

def create_korisnik(db: Session, korisnik: KorisnikCreate):
    hashed_password = pwd_context.hash(korisnik.password)
    db_korisnik = Korisnik(
        username=korisnik.username,
        email=korisnik.email, 
        hashed_password=hashed_password,
        ime=korisnik.ime,
        prezime=korisnik.prezime,
        adresa=korisnik.adresa,
        mobitel=korisnik.mobitel)
    db.add(db_korisnik)
    db.commit()
    db.refresh(db_korisnik)
    return db_korisnik


def authenticate_korisnik(db: Session, email:str, password: str):
    korisnik = get_korisnik_by_email(db, email)
    if not korisnik:
        return False
    if not pwd_context.verify(password, korisnik.hashed_password):
        return False
    return korisnik

def get_korisnik(db: Session, username: str):
    return db.query(Korisnik).filter(Korisnik.username == username).first()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_vozilo(db: Session, vozilo: schemas.VoziloCreate):
    db_vozilo = models.Vozilo(
        ime=vozilo.ime,
        godina=vozilo.godina,
        kilometraza=vozilo.kilometraza,
        cijena=vozilo.cijena,
        opis=vozilo.opis,
        slika=vozilo.slika,
        korisnik_id=vozilo.korisnik_id,
        model_id=vozilo.model_id,
        marka=vozilo.marka,
        abs=vozilo.abs,
        esp=vozilo.esp,
        airbags=vozilo.airbags,
        central_lock=vozilo.central_lock,
        power_windows=vozilo.power_windows,
        sunroof=vozilo.sunroof,
        navigation=vozilo.navigation,
        xenon_lights=vozilo.xenon_lights,
        leather_seats=vozilo.leather_seats,
        parking_sensors=vozilo.parking_sensors,
        backup_camera=vozilo.backup_camera,
        heated_seats=vozilo.heated_seats,
        bluetooth=vozilo.bluetooth,
        cruise_control=vozilo.cruise_control,
        automatic_climate_control=vozilo.automatic_climate_control,
        tire_size=vozilo.tire_size,
        car_color=vozilo.car_color,
        fuel_type=vozilo.fuel_type,
        transmission_type=vozilo.transmission_type,
        drive_type=vozilo.drive_type,
        number_of_doors=vozilo.number_of_doors,
        number_of_seats=vozilo.number_of_seats,
        engine_size=vozilo.engine_size,
        horsepower=vozilo.horsepower,
        torque=vozilo.torque,
        co2_emissions=vozilo.co2_emissions,
        fuel_consumption_city=vozilo.fuel_consumption_city,
        fuel_consumption_highway=vozilo.fuel_consumption_highway,
        fuel_consumption_combined=vozilo.fuel_consumption_combined
    )

    db.add(db_vozilo)
    db.commit()
    db.refresh(db_vozilo)
    return db_vozilo


def get_korisnik_by_id(db: Session, user_id: int):
    return db.query(models.Korisnik).filter(models.Korisnik.id == user_id).first()

def add_favorite(db: Session, korisnik_id: int, vozilo_id: int):
    # Create a new favorite record
    favorite = Favorit(korisnik_id=korisnik_id, vozilo_id=vozilo_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite

def remove_favorite(db: Session, korisnik_id: int, vozilo_id: int):
    favorite = db.query(Favorit).filter(
        Favorit.korisnik_id == korisnik_id,
        Favorit.vozilo_id == vozilo_id
    ).first()
    if favorite:
        db.delete(favorite)
        db.commit()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def update_korisnik(
    db: Session,
    user_id: int,
    username: str,
    ime: str,
    prezime: str,
    email: str,
    mobitel: str,
    adresa: str,
    password: str = None
):
    user = db.query(Korisnik).filter(Korisnik.id == user_id).first()

    if not user:
        return None 


    user.username = username
    user.ime = ime
    user.prezime = prezime
    user.email = email
    user.mobitel = mobitel
    user.adresa = adresa

    if password:
        hashed_password = pwd_context.hash(password)
        user.password = hashed_password

    db.commit()
    db.refresh(user)

    return user
