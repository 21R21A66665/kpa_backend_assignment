import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import date

## 1. NEW IMPORTS FOR DATADOG
from datadog_api_client.v2 import ApiClient, ApiException, Configuration
from datadog_api_client.v2.api import logs_api
from datadog_api_client.v2.models import HTTPLog, HTTPLogItem

# --- Environment and Database Setup ---
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

# --- FastAPI App and CORS Middleware ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## 2. NEW DATADOG CONFIGURATION
# This sets up the connection to Datadog using your API key from the .env file.
configuration = Configuration()
api_client = ApiClient(configuration)
logs_client = logs_api.LogsApi(api_client)

def log_to_datadog(level: str, message: str, attributes: dict = {}):
    """A helper function to easily send logs to Datadog."""
    try:
        body = HTTPLog(
            [
                HTTPLogItem(
                    ddsource="python",
                    ddtags=f"level:{level}", # This tag is how we will filter by INFO, WARNING, ERROR
                    hostname="kpa-backend-assignment",
                    message=message,
                    service="fastapi-service",
                    **attributes, # Add any extra data we want to log
                ),
            ]
        )
        logs_client.submit_log(body)
        print(f"Sent {level} log to Datadog: {message}")
    except ApiException as e:
        print(f"Error sending log to Datadog: {e}")


# --- Database Table Definition ---
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

# --- Pydantic Models ---
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

# --- Helper Function ---
def to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

# --- API Endpoints (Now with Logging) ---
@app.post("/api/users/login/")
def login_user(login_data: UserLogin, request: Request):
    client_host = request.client.host
    log_attributes = {"user_phone": login_data.phone, "client_ip": client_host}

    if login_data.phone == "7760873976" and login_data.password == "to_share@123":
        ## INFO log for a successful event
        log_to_datadog("INFO", f"Successful login for user {login_data.phone}", log_attributes)
        return {"success": True, "message": "Login Successful", "data": {"token": "dummy-token"}}
    
    ## WARNING log for a potential issue (a failed login attempt)
    log_to_datadog("WARNING", f"Failed login attempt for user {login_data.phone}", log_attributes)
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/forms/wheel-specifications", status_code=201)
def create_wheel_specification(spec: WheelSpecificationIn, db: Session = Depends(get_db)):
    try:
        insert_data = {
            "form_number": spec.formNumber, "submitted_by": spec.submittedBy, "submitted_date": spec.submittedDate
        }
        for key, value in spec.fields.model_dump().items():
            insert_data[to_snake(key)] = value
        
        query = wheel_specifications_table.insert().values(**insert_data)
        db.execute(query)
        db.commit()

        ## INFO log for a successful form submission
        log_to_datadog("INFO", f"Successfully submitted wheel specification form {spec.formNumber}")
        return {"success": True, "message": "Wheel specification submitted successfully."}
    except Exception as e:
        ## ERROR log for a critical failure (like a database error)
        log_to_datadog("ERROR", f"Database error on wheel spec submission: {str(e)}", {"form_number": spec.formNumber})
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save data to the database.")

@app.get("/api/forms/wheel-specifications")
def get_wheel_specifications(db: Session = Depends(get_db), formNumber: Optional[str] = None, submittedBy: Optional[str] = None):
    query = wheel_specifications_table.select()
    if formNumber:
        query = query.where(wheel_specifications_table.c.form_number == formNumber)
    if submittedBy:
        query = query.where(wheel_specifications_table.c.submitted_by == submittedBy)
    
    results = [dict(row) for row in db.execute(query).mappings()]

    ## INFO log for a standard data fetch operation
    log_to_datadog("INFO", "Fetched wheel specification data.", {"filter_formNumber": formNumber or "None"})
    return {"success": True, "message": "Filtered wheel specification forms fetched successfully.", "data": results}