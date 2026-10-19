# AeroSecure AI Backend

This directory contains the FastAPI backend for the AeroSecure AI prototype. The API currently provides a health check and a temporary prediction endpoint. The prediction endpoint will later be connected to the trained scikit-learn model.

## Requirements

- Python 3.12
- A virtual environment located at `.venv` in the project root

From the `AeroSecure_AI_Starter` project root, install the backend packages:

```bash
.venv/bin/python -m pip install fastapi "uvicorn[standard]" pytest httpx
```

## Run the API

From the project root, run:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Endpoints

- `GET /` confirms that the backend is running.
- `GET /health` returns the API health status.
- `POST /predict` accepts supplier-order information and returns delivery-time prediction fields.
- `GET /docs` opens the interactive Swagger API documentation.

## Test the prediction endpoint

Open `http://127.0.0.1:8000/docs`, expand `POST /predict`, select **Try it out**, enter valid request data, and select **Execute**.

The current prediction service is a temporary placeholder. It uses `quoted_lead_time_days` as the predicted value and adds five days for the conservative value. Responses identify this behavior with:

```json
"model_source": "temporary-placeholder"
```

Will be replaced by the trained scikit-learn model after the model artifact is available.

## Run automated tests

From the project root, run:

```bash
.venv/bin/python -m pytest backend/tests -v
```

The current test suite verifies the health-check and prediction endpoints.

## Stop the development server

Press `Control+C` in the terminal running Uvicorn. If the process was suspended with `Control+Z`, run `fg` first and then press `Control+C`.
