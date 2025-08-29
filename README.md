# KPA Backend API Assignment

This project was completed by **[Yarram Koushik]**.

## Implemented APIs

I have successfully implemented the following APIs as required by the assignment:

1.  **`POST /api/users/login/`**: A functional dummy login endpoint to allow the frontend application to authenticate and proceed.
2.  **`POST /api/forms/wheel-specifications`**: Accepts a JSON body with wheel specification details from the frontend and saves them to the PostgreSQL database.
3.  **`GET /api/forms/wheel-specifications`**: Retrieves a list of all wheel specifications from the database and can be filtered by `formNumber` or `submittedBy`.

## Tech Stack

* **Language**: Python
* **Framework**: FastAPI
* **Database**: PostgreSQL
* **Key Libraries**: SQLAlchemy, Uvicorn, Pydantic, python-dotenv

## Setup Instructions

1.  Ensure Python and PostgreSQL are installed.
2.  Create a `.env` file in the main folder with database credentials (DB_USER, DB_PASSWORD, etc.).
3.  Install dependencies: `python -m pip install "fastapi[all]" psycopg2-binary sqlalchemy python-dotenv`
4.  Run the server: `python -m uvicorn main:app --reload`
