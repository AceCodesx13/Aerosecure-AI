# AeroSecure AI Backend
backend/ contains the FastAPI backend for the AeroSecure AI prototype. The API provides a health check and a prediction endpoint connected to our trained scikit model.
## Requirements
- Python 3.12
- A virtual environment located at `.venv` in the project root

From the `AeroSecure_AI_Starter` project root, install the backend packages:

```bash
.venv/bin/python -m pip install fastapi "uvicorn[standard]" pytest httpx
```

## Model artifact setup
The `/predict` endpoint is connected to the trained scikit-learn model. The model artifact is not stored in GitHub because of its size.

Before running the prediction endpoint, place the approved model at:

artifacts/releases/v1/model.joblib

Alternatively, set `AEROSECURE_MODEL_PATH` to the model's local location:

export AEROSECURE_MODEL_PATH="/path/to/model.joblib"

## Run the API
From the project root, run:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Endpoints
- `GET /` confirms that the backend is running.
- `GET /health` returns the API health status.
- `GET /orders` returns orders allowed for the provided user and role.
- `POST /maintenance/recommend` returns a supplier recommendation or escalation decision.
- `POST /predict` accepts supplier-order information and returns delivery-time prediction fields.
- `GET /docs` opens the interactive Swagger API documentation.

## Test the prediction endpoint
Open `http://127.0.0.1:8000/docs`, expand `POST /predict`, select **Try it out**, enter valid request data, and select **Execute**.

## Run automated tests
From the project root, run:

```bash
.venv/bin/python -m pytest backend/tests -v
```

The current test suite verifies the health check, prediction endpoint, input validation, role-based order access, access logging, and maintenance recommendations.

## Stop the development server
Press `Control+C` in the terminal running Uvicorn.
