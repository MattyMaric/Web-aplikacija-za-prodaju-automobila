from datetime import datetime
import shutil
from sqlite3 import IntegrityError
from typing import Optional
from passlib.context import CryptContext
from pathlib import Path
from fastapi import APIRouter, FastAPI, File, HTTPException, Depends, Request, Form, UploadFile, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from app import crud, models, schemas, auth
from starlette.middleware.sessions import SessionMiddleware
from app.database import SessionLocal, engine, Base
from app.models import Favorit, Kontakt, Korisnik, Vozilo
from app.auth import get_db

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




app = FastAPI()
router = APIRouter()
app.include_router(router)
templates = Jinja2Templates(directory="app/templates")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

Base.metadata.create_all(bind=engine)

def get_current_user(request: Request, db: Session = Depends(auth.get_db)):
    user_id = request.session.get("user_id")
    
    # Return None if user_id is not found in session
    if user_id is None:
        return None

    # Fetch the user from the database
    user = db.query(models.Korisnik).filter(models.Korisnik.id == user_id).first()
    
    if user:
        # Fetch user's favorite vehicle IDs
        favorite_ids = db.query(models.Favorit.vozilo_id).filter(models.Favorit.korisnik_id == user_id).all()
        user.favorite_ids = [fid[0] for fid in favorite_ids]

    # Return the user object
    return user


def require_login(request: Request, db: Session = Depends(auth.get_db)): #Sluzi kao provjera da je korisnik prijavljen u sustav
    user = get_current_user(request, db)
    if user is None:
        return None  
    return user

@app.get("/")
async def home_page(request: Request, db: Session = Depends(auth.get_db)):
    #dohvati korisnika ako je prijavljen
    user = get_current_user(request, db)
    
    # dobavljanje vrijednosti za dropdown meni
    marka = db.query(models.Marka).all()
    model = db.query(models.Model).all()
    godina = db.query(models.Vozilo.godina).distinct().all()
    max_cijena = db.query(models.Vozilo.cijena).distinct().order_by(models.Vozilo.cijena.desc()).all()
    kilometraza = db.query(models.Vozilo.kilometraza).distinct().all()
    
    # Dohvati nasumicno 5 vozila iz sustava
    odabrana_vozila = db.query(models.Vozilo).order_by(func.random()).limit(6).all()

    #Proslijedi informacije u template home.html
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,  # Pass the user object for user-related logic (if needed)
        "marke": marka,
        "modeli": model,
        "godina": godina,
        "max_cijena": max_cijena,
        "kilometraza": kilometraza,
        "odabrana_vozila": odabrana_vozila,
    })


app.add_middleware(SessionMiddleware, secret_key="a2a93538d055ee6763cef411cc034c46341fda05038c8b27614af20980fa561c") ##TODO: sakriti kljuc
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/updateProfile")
async def updateProfile(
    username: str = Form(...),
    ime: str = Form(...),
    prezime: str = Form(...),
    email: str = Form(...),
    mobitel: str = Form(...),
    adresa: str = Form(...),
    password: str = Form(None),  # Form(None) sluzi da promijena lozinke nije nužna, nego po potrebi korisnika
    db: Session = Depends(auth.get_db),
    current_user: Korisnik = Depends(require_login)
):
    user = db.query(Korisnik).filter(Korisnik.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Azuriraj informacije
    user.username = username
    user.ime = ime
    user.prezime = prezime
    user.email = email
    user.mobitel = mobitel
    user.adresa = adresa

    # Azuriraj lozinku ako je potrebno
    if password:
        hashed_password = crud.hash_password(password)  # Use the same hash function from signup
        user.hashed_password = hashed_password

    # Commit the changes
    db.commit()
    db.refresh(user)

    return RedirectResponse(url=f"/profile/{user.id}", status_code=303)



@app.get("/profile/{user_id}")
async def profile_page(
    request: Request, 
    user_id: int, 
    db: Session = Depends(auth.get_db), 
    current_user: models.Korisnik = Depends(get_current_user)  # Ensure this returns a Korisnik instance
):
    user = db.query(models.Korisnik).filter(models.Korisnik.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if current_user is a valid instance of Korisnik
    if current_user is not None:
        print(f"Current user ID: {current_user.id}, Viewing user ID: {user.id}")  # Should now work
    else:
        print("No current user found")

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "current_user": current_user  # Pass current user to the template
    })


@app.get("/create")
async def create_page(request: Request, db: Session = Depends(auth.get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        return RedirectResponse(url="/login")

    marke = db.query(models.Marka).all()
    modeli = db.query(models.Model).all()

    return templates.TemplateResponse("create.html", {
        "request": request,
        "marke": marke,
        "modeli": modeli,
    })

@app.post("/create_vozilo")
async def create_new_vozilo(
    ime: str = Form(...),
    model_id: int = Form(...),
    marka: int = Form(...),
    godina: int = Form(...),
    kilometraza: int = Form(...),
    cijena: float = Form(...),
    opis: Optional[str] = Form(...),
    slika: UploadFile = File(...),
    abs: bool = Form(False),
    esp: bool = Form(False),
    airbags: bool = Form(False),
    central_lock: bool = Form(False),
    power_windows: bool = Form(False),
    sunroof: bool = Form(False),
    navigation: bool = Form(False),
    xenon_lights: bool = Form(False),
    leather_seats: bool = Form(False),
    parking_sensors: bool = Form(False),
    backup_camera: bool = Form(False),
    heated_seats: bool = Form(False),
    bluetooth: bool = Form(False),
    cruise_control: bool = Form(False),
    automatic_climate_control: bool = Form(False),
    tire_size: Optional[str] = Form(None),
    car_color: Optional[str] = Form(None),
    fuel_type: Optional[str] = Form(None),
    transmission_type: Optional[str] = Form(None),
    drive_type: Optional[str] = Form(None),
    number_of_doors: int = Form(4),
    number_of_seats: int = Form(5),
    engine_size: Optional[float] = Form(None),
    horsepower: Optional[int] = Form(None),
    torque: Optional[int] = Form(None),
    co2_emissions: Optional[float] = Form(None),
    fuel_consumption_city: Optional[float] = Form(None),
    fuel_consumption_highway: Optional[float] = Form(None),
    fuel_consumption_combined: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.Korisnik = Depends(require_login)
):
    #Direktorij za spremanje slika vozila
    upload_dir = Path("app/static/uploads/")
    upload_dir.mkdir(parents=True, exist_ok=True)
    image_directory = Path("/static/uploads/") #Direktorij za citanje slika iz direktorija i prikaz na templateu

    # Sanitize filename
    sanitized_filename = slika.filename.replace(" ", "_")  # Sanitizacija naziva datoteke
    image_path = upload_dir / sanitized_filename  # Putanja za spremanje
    image_location = str(image_directory / sanitized_filename)  #Putanja za citanje

    try: #spremanje datoteke u foldere
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(slika.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Provjera da su sva polja popunjena
    if not all([ime, model_id, marka, godina, kilometraza, cijena]):
        raise HTTPException(status_code=400, detail="All required fields must be filled.")

    vozilo_data = schemas.VoziloCreate(
        ime=ime,
        model_id=model_id,
        marka=marka,
        godina=godina,
        kilometraza=kilometraza,
        cijena=cijena,
        opis=opis,
        slika=image_location,
        abs=abs,
        esp=esp,
        airbags=airbags,
        central_lock=central_lock,
        power_windows=power_windows,
        sunroof=sunroof,
        navigation=navigation,
        xenon_lights=xenon_lights,
        leather_seats=leather_seats,
        parking_sensors=parking_sensors,
        backup_camera=backup_camera,
        heated_seats=heated_seats,
        bluetooth=bluetooth,
        cruise_control=cruise_control,
        automatic_climate_control=automatic_climate_control,
        tire_size=tire_size,
        car_color=car_color,
        fuel_type=fuel_type,
        transmission_type=transmission_type,
        drive_type=drive_type,
        number_of_doors=number_of_doors,
        number_of_seats=number_of_seats,
        engine_size=engine_size,
        horsepower=horsepower,
        torque=torque,
        co2_emissions=co2_emissions,
        fuel_consumption_city=fuel_consumption_city,
        fuel_consumption_highway=fuel_consumption_highway,
        fuel_consumption_combined=fuel_consumption_combined,
        korisnik_id=current_user.id
    )

    vozilo = crud.create_vozilo(db=db, vozilo=vozilo_data)

    return RedirectResponse(url="/", status_code=302)


@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(auth.get_db)
):

    user = crud.authenticate_korisnik(db, email=email, password=password)
    
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid email or password"}
        )
    
    user_pydantic = schemas.Korisnik.model_validate(user)
    
    request.session["user_id"] = user_pydantic.id
    request.session["username"] = user_pydantic.username
    
    return RedirectResponse(url="/welcome", status_code=302)


@app.get("/welcome")
async def welcome_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  
    return RedirectResponse(url="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/models/{marka_id}")
def get_models_by_marka(marka_id: int, db: Session = Depends(get_db)):
    models_list = db.query(models.Model).filter(models.Model.marka_id == marka_id).all()
    return models_list

@app.get("/", response_class=HTMLResponse)
async def car_list(request: Request, db: Session = Depends(auth.get_db)):
    cars = db.query(models.Vozilo).all()
    return templates.TemplateResponse("car_list.html", {"request": request, "cars": cars})

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

@app.get("/vozilo/{vozilo_id}")
async def vozilo_detail(
    request: Request,
    vozilo_id: int,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_login)
):
    vozilo = db.query(models.Vozilo).filter(models.Vozilo.id == vozilo_id).first()
    if not vozilo:
        raise HTTPException(status_code=404, detail="Vozilo nije pronađeno")
    
    if current_user:
        is_favorite = db.query(models.Favorit).filter(
            models.Favorit.korisnik_id == current_user.id,
            models.Favorit.vozilo_id == vozilo_id
        ).first() is not None

        is_creator = vozilo.korisnik_id == current_user.id
        is_logged_in = True
    else:
        is_favorite = False
        is_creator = False
        is_logged_in = False

    return templates.TemplateResponse("vozilodetail.html", {
        "request": request,
        "vozilo": vozilo,
        "is_favorite": is_favorite,
        "is_creator": is_creator,
        "is_logged_in": is_logged_in
    })



@app.get("/editProfile")
async def edit_profile(request: Request, db: Session = Depends(get_db), current_user: Korisnik = Depends(require_login)):
    user = db.query(Korisnik).filter(Korisnik.id == current_user.id).first()
    
    if not user:
        return {"error": "User not found"}
    
    return templates.TemplateResponse("editProfile.html", {"request": request, "user": user})

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/updateProfile")
async def updateProfile(
    request: Request,
    username: str = Form(...),
    ime: str = Form(...),
    prezime: str = Form(...),
    email: str = Form(...),
    mobitel: str = Form(...),
    adresa: str = Form(...),
    password: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Korisnik = Depends(require_login)
):
    user = db.query(Korisnik).filter(Korisnik.id == current_user.id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update other fields
    user.username = username
    user.ime = ime
    user.prezime = prezime
    user.email = email
    user.mobitel = mobitel
    user.adresa = adresa

    if password:
        hashed_password = pwd_context.hash(password)
        user.password = hashed_password

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        print(f"Error committing changes: {e}")
        raise HTTPException(status_code=500, detail="Error updating profile")

    updated_user = db.query(Korisnik).filter(Korisnik.id == current_user.id).first()
    print(f"Updated user password in DB: {updated_user.password}")

    return RedirectResponse(url="/profile", status_code=303)


def require_admin(request: Request, db: Session = Depends(auth.get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        return RedirectResponse(url="/login") 

    user = db.query(models.Korisnik).filter(models.Korisnik.id == user_id).first()
    if user is None or user.tip_korisnika != 'Admin':
        return RedirectResponse(url="/login")  


@app.get("/admin")
async def admin_dashboard(
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)  #Pristup stranici moguce samo uz ulogu administratora
):
    # Dohvacanje podataka za admin dashboard
    vozila = db.query(models.Vozilo).all()
    korisnici = db.query(models.Korisnik).all()

    # proslijedi informacije na template
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "vozila": vozila,
        "korisnici": korisnici,
        "current_user": current_user
    })

@app.get("/admin/edit_vozilo/{vozilo_id}")
async def edit_vozilo_page(
    vozilo_id: int,
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)
):
    # Dohvacanje odredenog vozila
    vozilo = db.query(models.Vozilo).filter(models.Vozilo.id == vozilo_id).first()

    # Dohvacanje svih proizvodaca i modela
    marka = db.query(models.Marka).all()  # Assuming the Manufacturer table exists
    car_models = db.query(models.Model).all()  # Renamed variable to avoid conflict

    # U slucaju ako vozilo nije pronadeno
    if not vozilo:
        raise HTTPException(status_code=404, detail="Car not found")

    return templates.TemplateResponse("edit_vozilo.html", {
        "request": request,
        "vozilo": vozilo,
        "current_user": current_user,
        "marka": marka,
        "models": car_models 
    })


@app.post("/admin/edit_vozilo/{vozilo_id}")
async def update_vozilo(
    vozilo_id: int,
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)
):
    form_data = await request.form()

    vozilo = db.query(models.Vozilo).filter(models.Vozilo.id == vozilo_id).first()
    if not vozilo:
        raise HTTPException(status_code=404, detail="Car not found")

    vozilo.ime = form_data['ime']
    vozilo.marka = form_data['marka']
    vozilo.model_id = form_data['model_id']
    vozilo.godina = form_data['godina']
    vozilo.cijena = form_data['cijena']
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/delete_vozilo/{vozilo_id}")
async def delete_vozilo(
    vozilo_id: int,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)
):
    vozilo = db.query(models.Vozilo).filter(models.Vozilo.id == vozilo_id).first()

    if not vozilo:
        raise HTTPException(status_code=404, detail="Car not found")

    db.delete(vozilo)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/edit_user/{korisnik_id}")
async def edit_user_page(
    korisnik_id: int,
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)
):
    korisnik = db.query(models.Korisnik).filter(models.Korisnik.id == korisnik_id).first()

    if not korisnik:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("editKorisnikAdmin.html", {
        "request": request,
        "korisnik": korisnik,
        "current_user": current_user
    })


@app.post("/admin/edit_user/{korisnik_id}")
async def edit_user_submit(
    korisnik_id: int,
    request: Request,
    username: str = Form(...),
    tip_korisnika: str = Form(...),
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)
):
    korisnik = db.query(models.Korisnik).filter(models.Korisnik.id == korisnik_id).first()

    if not korisnik:
        raise HTTPException(status_code=404, detail="User not found")

    
    korisnik.username = username
    korisnik.tip_korisnika = tip_korisnika

    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/delete_user/{korisnik_id}")
async def delete_user(
    korisnik_id: int,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_admin)
):
    korisnik = db.query(models.Korisnik).filter(models.Korisnik.id == korisnik_id).first()

    if not korisnik:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(korisnik)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.get("/search")
async def search_vozila(
    request: Request,
    db: Session = Depends(auth.get_db),
    search_query: str = Query(None),
    marka: str = Query(None)
):
    query = db.query(models.Vozilo)

    if search_query:
        query = query.filter(models.Vozilo.ime.ilike(f"%{search_query}%"))
    
    if marka:
        query = query.filter(models.Vozilo.marka.ilike(f"%{marka}%"))
    
    vozila = query.all()

    return templates.TemplateResponse("search.html", {
        "request": request,
        "vozila": vozila,
        "search_query": search_query,
        "marka": marka
    })

@app.get("/quicksearch")
async def quick_search(
    request: Request,
    marka: int = None,
    model: int = None,
    min_cijena: str = None,
    max_cijena: str = None,
    db: Session = Depends(auth.get_db)
):
    query = db.query(models.Vozilo)

    if marka is not None:
        try:
            query = query.filter(models.Vozilo.marka == marka)
        except ValueError:
            raise HTTPException(status_code=400, detail="Marka must be a valid integer.")

    if model is not None:
        try:
            query = query.filter(models.Vozilo.model_id == model)
        except ValueError:
            raise HTTPException(status_code=400, detail="Model must be a valid integer.")

    if min_cijena:
        try:
            min_cijena_float = float(min_cijena)
        except ValueError:
            raise HTTPException(status_code=400, detail="Min Cijena must be a valid number.")

    if max_cijena:
        try:
            max_cijena_float = float(max_cijena)
            query = query.filter(models.Vozilo.cijena <= max_cijena_float)
        except ValueError:
            raise HTTPException(status_code=400, detail="Max Cijena must be a valid number.")

    results = query.all()

    return templates.TemplateResponse("quicksearch.html", {
        "request": request,
        "vehicles": results,
        "marka": marka,
        "model": model,
        "min_cijena": min_cijena,
        "max_cijena": max_cijena
    })



@app.get("/models/{marka_id}")
async def get_models(marka_id: int, db: Session = Depends(auth.get_db)):
    models = db.query(models.Model).filter(models.Model.marka_id == marka_id).all()

    return [{"id": model.id, "naziv_modela": model.naziv_modela} for model in models]


@app.get("/kupnja/{car_id}")
async def payment_page(request: Request, car_id: int, db: Session = Depends(auth.get_db)):
    car = db.query(models.Vozilo).filter(models.Vozilo.id == car_id).first()

    if not car:
        return templates.TemplateResponse("greska.html", {
            "request": request,
            "message": "Vozilo nije pronadeno, pokusajte ponovo!"
        })

    return templates.TemplateResponse("placanje.html", {
        "request": request,
        "car": car
    })

@app.post("/process_payment/{car_id}")
async def process_payment(car_id: int, request: Request, db: Session = Depends(auth.get_db)):
    form_data = await request.form()
    credit_card = form_data.get('credit_card')
    expiry_date = form_data.get('expiry_date')
    cvv = form_data.get('cvv')

    logger.info(f"Processing payment for car ID: {car_id}")
    logger.debug(f"Received payment details: credit_card={credit_card}, expiry_date={expiry_date}, cvv={cvv}")

    # Attempt to delete the favorite car entry
    db.query(models.Favorit).filter(models.Favorit.vozilo_id == car_id).delete()
    logger.info(f"Deleted favorite entry for car ID: {car_id}")
    
    # Check if payment details are provided
    if credit_card and expiry_date and cvv:
        # Fetch the car based on car_id
        car = db.query(models.Vozilo).filter(models.Vozilo.id == car_id).first()
        
        if car:
            kupac_id = request.session.get("user_id")
            prodavac_id = car.korisnik_id 
            cijena = car.cijena

            logger.info(f"Found car: {car.ime}, buyer ID: {kupac_id}, seller ID: {prodavac_id}, price: {cijena}")

            # Create a new transaction
            new_transaction = models.Transakcija(
                kupac_id=kupac_id,
                prodavac_id=prodavac_id,
                vozilo_id=car_id,
                datum_transakcije=datetime.now(),
                cijena=cijena
            )
            db.add(new_transaction)
            logger.info(f"Added transaction for car: {car.ime}")

            # Delete the car after adding the transaction
            db.delete(car)
            logger.info(f"Deleted car after transaction for car ID: {car_id}")

            # Commit changes to the database
            try:
                db.commit()
                logger.info("Transaction committed successfully.")
                return templates.TemplateResponse("uspjesno.html", {
                    "request": request,
                    "message": f"Transakcija uspješna za: {car.ime}!"
                })
            except IntegrityError as e:
                db.rollback()  # Rollback the transaction on error
                logger.error(f"IntegrityError: {e}")
                return templates.TemplateResponse("greska.html", {
                    "request": request,
                    "message": "Greška pri spremanju transakcije!"
                })
        else:
            logger.warning(f"Car not found for ID: {car_id}")
            return templates.TemplateResponse("greska.html", {
                "request": request,
                "message": "Vozilo nije pronađeno!"
            })
    else:
        logger.warning("Invalid payment details provided.")
        return templates.TemplateResponse("greska.html", {
            "request": request,
            "message": "Pogrešni detalji plaćanja!"
        })

@app.get("/edit_vozilo/{vozilo_id}")
async def edit_vozilo_page(
    vozilo_id: int,
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_login)
):
    vozilo = db.query(models.Vozilo).filter(models.Vozilo.id == vozilo_id).first()

    marka = db.query(models.Marka).all() 
    car_models = db.query(models.Model).all()


    if not vozilo:
        raise HTTPException(status_code=404, detail="Car not found")

    return templates.TemplateResponse("edit_vozilo.html", {
        "request": request,
        "vozilo": vozilo,
        "current_user": current_user,
        "marka": marka,
        "models": car_models
    })

@app.post("/edit_vozilo/{vozilo_id}")
async def update_vozilo(
    vozilo_id: int,
    ime: str = Form(...), 
    marka: int = Form(...),
    model_id: int = Form(...),
    godina: str = Form(...),
    cijena: str = Form(...),
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_login)
):
    vozilo = db.query(models.Vozilo).filter(models.Vozilo.id == vozilo_id).first()

    if not vozilo:
        raise HTTPException(status_code=404, detail="Car not found")

    vozilo.ime = ime
    vozilo.marka = marka
    vozilo.model_id = model_id
    vozilo.godina = godina
    vozilo.cijena = cijena
    db.commit()

    return RedirectResponse(url="/", status_code=303)


@app.post("/favorites/{vozilo_id}")
async def toggle_favorite(
    vozilo_id: int,
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/login")

    # Provjeri da li je vec u favoritima
    existing_favorite = db.query(models.Favorit).filter(
        models.Favorit.korisnik_id == current_user.id,
        models.Favorit.vozilo_id == vozilo_id
    ).first()

    if existing_favorite:
        # Ako je auto vec u favoritima, izbrisi ga
        db.delete(existing_favorite)
    else:
        # Ako nije u favoritima, dodaj ga u favorite
        new_favorite = models.Favorit(korisnik_id=current_user.id, vozilo_id=vozilo_id)
        db.add(new_favorite)

    db.commit()
    return RedirectResponse(url=f"/vozilo/{vozilo_id}", status_code=302)

@app.get("/contact")
async def contact_page(request: Request):

    return templates.TemplateResponse("kontakt.html", {"request": request})

@app.post("/submit_contact")
async def submit_contact(request: Request, message: str = Form(...), db: Session = Depends(get_db)):

    korisnik_id = request.session.get("user_id")
    
    if not korisnik_id:
        return RedirectResponse(url="/login", status_code=303)

    current_datetime = datetime.now()

    new_contact = Kontakt(
        korisnik_id=korisnik_id, 
        poruka=message,
        datum_slanja=current_datetime) 
    db.add(new_contact)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

@app.get("/admin/messages")
async def get_messages(request: Request, db: Session = Depends(get_db), current_user: models.Korisnik = Depends(require_admin)):
    messages = db.query(Kontakt).all()

    return templates.TemplateResponse("kontaktporuke.html", {"request": request, "messages": messages})

@app.post("/admin/messages/delete/{message_id}")
async def delete_message(message_id: int, db: Session = Depends(get_db), current_user: models.Korisnik = Depends(require_admin)):
    message = db.query(Kontakt).filter(Kontakt.id == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()

    return RedirectResponse(url="/admin/messages", status_code=303)


@app.get("/favorites", response_class=HTMLResponse)
async def get_favorites(
    request: Request,
    db: Session = Depends(auth.get_db),
    current_user: models.Korisnik = Depends(require_login)
):
    favorites = (
        db.query(Vozilo)
        .join(Favorit, Favorit.vozilo_id == Vozilo.id)
        .filter(Favorit.korisnik_id == current_user.id)
        .all()
    )

    return templates.TemplateResponse(
        "favorites.html", {"request": request, "favorites": favorites, "current_user": current_user}
    )
