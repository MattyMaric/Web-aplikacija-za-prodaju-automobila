from sqlalchemy import Boolean, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Korisnik(Base):
    __tablename__ = 'korisnik'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    ime = Column(String(50), nullable=False)
    prezime = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(60), nullable=False)
    mobitel = Column(String(20), nullable=True)
    adresa = Column(String(200), nullable=True)
    tip_korisnika = Column(String(20), nullable=False, default="Korisnik") 
    datum_registracije = Column(DateTime, default=datetime.now)

    vozila = relationship('Vozilo', back_populates='korisnik')
    favoriti = relationship('Favorit', back_populates='korisnik')
    transakcije_kupac = relationship('Transakcija', foreign_keys='Transakcija.kupac_id', back_populates='kupac')
    transakcije_prodavac = relationship('Transakcija', foreign_keys='Transakcija.prodavac_id', back_populates='prodavac')
    kontakt = relationship('Kontakt', back_populates='korisnik')

class Marka(Base):
    __tablename__ = 'marka'

    id = Column(Integer, primary_key=True, index=True)
    ime = Column(String(50), nullable=False)

    model = relationship('Model', back_populates='marka')

class Model(Base):
    __tablename__ = 'model'

    id = Column(Integer, primary_key=True, index=True)
    marka_id = Column(Integer, ForeignKey('marka.id'), nullable=False)
    naziv_modela = Column(String(50), nullable=False)

    marka = relationship('Marka', back_populates='model')

    vozila = relationship('Vozilo', back_populates='model')

class Vozilo(Base):
    __tablename__ = 'vozilo'

    id = Column(Integer, primary_key=True, index=True)
    ime = Column(String(100), nullable=False)
    marka = Column(Integer, ForeignKey('marka.id'), nullable=False)
    model_id = Column(Integer, ForeignKey('model.id'), nullable=False)
    godina = Column(Integer, nullable=False)
    kilometraza = Column(Integer, nullable=False)
    cijena = Column(Float, nullable=False)
    opis = Column(Text, nullable=True)
    slika = Column(String(100), nullable=False)
    korisnik_id = Column(Integer, ForeignKey('korisnik.id'), nullable=False)

    abs = Column(Boolean, default=False)
    esp = Column(Boolean, default=False)
    airbags = Column(Boolean, default=False)
    central_lock = Column(Boolean, default=False)
    power_windows = Column(Boolean, default=False)
    sunroof = Column(Boolean, default=False)
    navigation = Column(Boolean, default=False)
    xenon_lights = Column(Boolean, default=False)
    leather_seats = Column(Boolean, default=False)
    parking_sensors = Column(Boolean, default=False)
    backup_camera = Column(Boolean, default=False)
    heated_seats = Column(Boolean, default=False)
    bluetooth = Column(Boolean, default=False)
    cruise_control = Column(Boolean, default=False)
    automatic_climate_control = Column(Boolean, default=False)

    tire_size = Column(String(50), nullable=True)
    car_color = Column(String(50), nullable=True)
    fuel_type = Column(String(50), nullable=True)
    transmission_type = Column(String(50), nullable=True)
    drive_type = Column(String(50), nullable=True)
    number_of_doors = Column(Integer, nullable=False, default=4)
    number_of_seats = Column(Integer, nullable=False, default=5)
    engine_size = Column(Float, nullable=True)
    horsepower = Column(Integer, nullable=True)
    torque = Column(Integer, nullable=True)

    co2_emissions = Column(Float, nullable=True)
    fuel_consumption_city = Column(Float, nullable=True)
    fuel_consumption_highway = Column(Float, nullable=True)
    fuel_consumption_combined = Column(Float, nullable=True)

    infotainment_system = Column(Boolean, default=False)
    keyless_entry = Column(Boolean, default=False)
    start_stop_system = Column(Boolean, default=False)
    panoramic_roof = Column(Boolean, default=False)
    lane_assist = Column(Boolean, default=False)
    blind_spot_monitor = Column(Boolean, default=False)

    model = relationship('Model', back_populates='vozila')
    korisnik = relationship('Korisnik', back_populates='vozila')
    favoriti = relationship('Favorit', back_populates='vozilo')
    transakcije = relationship('Transakcija', back_populates='vozilo')

class Favorit(Base):
    __tablename__ = 'favorit'

    id = Column(Integer, primary_key=True, index=True)
    korisnik_id = Column(Integer, ForeignKey('korisnik.id'), nullable=False)
    vozilo_id = Column(Integer, ForeignKey('vozilo.id'), nullable=False)

    korisnik = relationship('Korisnik', back_populates='favoriti')
    vozilo = relationship('Vozilo', back_populates='favoriti')

class Transakcija(Base):
    __tablename__ = 'transakcija'

    id = Column(Integer, primary_key=True, index=True)
    kupac_id = Column(Integer, ForeignKey('korisnik.id'), nullable=False)
    prodavac_id = Column(Integer, ForeignKey('korisnik.id'), nullable=False)
    vozilo_id = Column(Integer, ForeignKey('vozilo.id'), nullable=False)
    datum_transakcije = Column(DateTime, default=timezone.utc)
    cijena = Column(Float, nullable=False)

    kupac = relationship('Korisnik', foreign_keys=[kupac_id], back_populates='transakcije_kupac')
    prodavac = relationship('Korisnik', foreign_keys=[prodavac_id], back_populates='transakcije_prodavac')
    vozilo = relationship('Vozilo', back_populates='transakcije')

class Kontakt(Base):
    __tablename__ = 'kontakt'

    id = Column(Integer, primary_key=True, index=True)
    korisnik_id = Column(Integer, ForeignKey('korisnik.id'), nullable=False)
    poruka = Column(Text, nullable=False)
    datum_slanja = Column(DateTime, default=timezone.utc)

    korisnik = relationship('Korisnik', back_populates='kontakt')
