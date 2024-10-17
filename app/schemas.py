from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime

class KorisnikBase(BaseModel):
    email: EmailStr
    username: str
    ime: str
    prezime: str
    mobitel: Optional[str] = None
    adresa: Optional[str] = None
    tip_korisnika: str = "Korisnik"

class VoziloBase(BaseModel):
    ime: str
    naziv: str
    model: str
    marka: str
    godina: int
    kilometraza: int
    cijena: float
    opis: Optional[str] = None
    slika: Optional[str] = None

class KategorijaBase(BaseModel):
    ime: str

class FavoritBase(BaseModel):
    korisnik_id: int
    vozilo_id: int

class TransakcijaBase(BaseModel):
    cijena: float

class RecenzijaBase(BaseModel):
    ocjena: int
    komentar: Optional[str] = None

class PorukaBase(BaseModel):
    sadrzaj: str

class KorisnikCreate(KorisnikBase):
    password: str

class VoziloCreate(BaseModel):
    ime: str
    model_id: int
    marka: int
    godina: int
    kilometraza: int
    cijena: float
    opis: Optional[str] = None
    slika: str
    abs: Optional[bool] = False
    esp: Optional[bool] = False
    airbags: Optional[bool] = False
    central_lock: Optional[bool] = False
    power_windows: Optional[bool] = False
    sunroof: Optional[bool] = False
    navigation: Optional[bool] = False
    xenon_lights: Optional[bool] = False
    leather_seats: Optional[bool] = False
    parking_sensors: Optional[bool] = False
    backup_camera: Optional[bool] = False
    heated_seats: Optional[bool] = False
    bluetooth: Optional[bool] = False
    cruise_control: Optional[bool] = False
    automatic_climate_control: Optional[bool] = False
    tire_size: Optional[str] = None
    car_color: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission_type: Optional[str] = None
    drive_type: Optional[str] = None
    number_of_doors: int = 4
    number_of_seats: int = 5
    engine_size: Optional[float] = None
    horsepower: Optional[int] = None
    torque: Optional[int] = None
    co2_emissions: Optional[float] = None
    fuel_consumption_city: Optional[float] = None
    fuel_consumption_highway: Optional[float] = None
    fuel_consumption_combined: Optional[float] = None
    korisnik_id: int

class KategorijaCreate(KategorijaBase):
    pass

class FavoritCreate(FavoritBase):
    pass

class TransakcijaCreate(TransakcijaBase):
    kupac_id: int
    prodavac_id: int
    vozilo_id: int

class RecenzijaCreate(RecenzijaBase):
    korisnik_id: int
    vozilo_id: int

class PorukaCreate(PorukaBase):
    posiljatelj_id: int
    primatelj_id: int

class Korisnik(KorisnikBase):
    id: int
    datum_registracije: datetime

    class Config:
        from_attributes = True

class Vozilo(VoziloBase):
    id: int
    korisnik_id: int

    class Config:
        from_attributes = True

class Kategorija(KategorijaBase):
    id: int

    class Config:
        from_attributes = True

class Favorit(FavoritBase):
    id: int

    class Config:
        from_attributes = True

class Transakcija(TransakcijaBase):
    id: int
    datum_transakcije: datetime
    kupac_id: int
    prodavac_id: int
    vozilo_id: int

    class Config:
        from_attributes = True

class Recenzija(RecenzijaBase):
    id: int
    datum_recenzije: datetime
    korisnik_id: int
    vozilo_id: int

    class Config:
        from_attributes = True

class Poruka(PorukaBase):
    id: int
    datum_slanja: datetime
    posiljatelj_id: int
    primatelj_id: int

    class Config:
        from_attributes = True
