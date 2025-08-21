import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import date


load_dotenv()
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


metadata = sqlalchemy.MetaData()
wheel_specifications_table = sqlalchemy.Table(
    "wheel_specifications", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("form_number", sqlalchemy.String),
    sqlalchemy.Column("submitted_by", sqlalchemy.String),
    sqlalchemy.Column("submitted_date", sqlalchemy.Date),
    sqlalchemy.Column("axle_box_housing_bore_dia", sqlalchemy.String),
    sqlalchemy.Column("bearing_seat_diameter", sqlalchemy.String),
    sqlalchemy.Column("condemning_dia", sqlalchemy.String),
    sqlalchemy.Column("intermediate_wwp", sqlalchemy.String),
    sqlalchemy.Column("last_shop_issue_size", sqlalchemy.String),
    sqlalchemy.Column("roller_bearing_bore_dia", sqlalchemy.String),
    sqlalchemy.Column("roller_bearing_outer_dia", sqlalchemy.String),
    sqlalchemy.Column("roller_bearing_width", sqlalchemy.String),
    sqlalchemy.Column("tread_diameter_new", sqlalchemy.String),
    sqlalchemy.Column("variation_same_axle", sqlalchemy.String),
    sqlalchemy.Column("variation_same_bogie", sqlalchemy.String),
    sqlalchemy.Column("variation_same_coach", sqlalchemy.String),
    sqlalchemy.Column("wheel_disc_width", sqlalchemy.String),
    sqlalchemy.Column("wheel_gauge", sqlalchemy.String),
    sqlalchemy.Column("wheel_profile", sqlalchemy.String),
)


class WheelFields(BaseModel):
    axleBoxHousingBoreDia: str
    bearingSeatDiameter: str
    condemningDia: str
    intermediateWwp: str
    lastShopIssueSize: str
    rollerBearingBoreDia: str
    rollerBearingOuterDia: str
    rollerBearingWidth: str
    treadDiameterNew: str
    variationSameAxle: str
    variationSameBogie: str
    variationSameCoach: str
    wheelDiscWidth: str
    wheelGauge: str
    wheelProfile: str

class WheelSpecificationIn(BaseModel):
    fields: WheelFields
    formNumber: str
    submittedBy: str
    submittedDate: date 

class UserLogin(BaseModel):
    phone: str
    password: str


def to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

# --- API Endpoints ---
@app.post("/api/users/login/")
def login_user(login_data: UserLogin):
    if login_data.phone == "7760873976" and login_data.password == "to_share@123":
        return {"success": True, "message": "Login Successful", "data": {"token": "dummy-token"}}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/forms/wheel-specifications", status_code=201)
def create_wheel_specification(spec: WheelSpecificationIn, db: Session = Depends(get_db)):
    print("\n--- DATA RECEIVED FROM FRONTEND ---")
    print(spec.model_dump_json(indent=2))

    insert_data = {
        "form_number": spec.formNumber,
        "submitted_by": spec.submittedBy,
        "submitted_date": spec.submittedDate,
    }
    for key, value in spec.fields.model_dump().items():
        insert_data[to_snake(key)] = value

    print("\n--- DATA BEING SENT TO DATABASE ---")
    print(insert_data)

    try:
        query = wheel_specifications_table.insert().values(**insert_data)
        db.execute(query)
        db.commit()
        print("\n--- DATABASE COMMIT SUCCESSFUL ---")
        return {"success": True, "message": "Wheel specification submitted successfully."}
    except Exception as e:
        print("\n---!!! DATABASE ERROR !!! ---")
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save data to the database.")

@app.get("/api/forms/wheel-specifications")
def get_wheel_specifications(db: Session = Depends(get_db), formNumber: Optional[str] = None, submittedBy: Optional[str] = None):
   
    pass 