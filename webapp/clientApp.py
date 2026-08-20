from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
from PatientReadmissionPredictor import PatientReadmissionPredictor
import encodedValues
import os
from datetime import datetime
from pythonScripts.monitor import run_drift   #run drift detection


logging.basicConfig(
    filename='app.log', 
    filemode='a', # 'a' to append logs, 'w' to overwrite every run
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO # Capture INFO, WARNING, ERROR, and CRITICAL
)
logger = logging.getLogger('clientApp')

app=FastAPI()

_WEBAPP_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _WEBAPP_DIR / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

def _html_response(request: Request, template_name: str, context: dict) -> HTMLResponse:
    response = templates.TemplateResponse(request, template_name, context)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return _html_response(
        request,
        "index.html",
        {"encoded": encodedValues.encoded},
    )

@app.post("/predict")
async def predict(request: Request):
    logger.info(f"Running prediction")
    try:
        body_json = await request.json()
        #logger.info(f"requestBody:{body_json}")
        patientRecord={}
        for key, value in body_json.items():
            #logger.info(f"ClientAPP: {key}: {value}")   
            modelFeatureName,encodedValue=encodedValues.get_encodedValue(key,value)
            patientRecord[modelFeatureName]=encodedValue
        
        #logger.info(f"final patientRecord for prediction: {patientRecord}")
        result=PatientReadmissionPredictor().predict_patient_readmission(patientRecord)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring", response_class=HTMLResponse)
async def dashboard(request: Request):
    logger.info("Running drift detection")
    try:
        drift_summary = run_drift(output_path=os.getenv("DRIFT_RESULTS_FILE"))
        logger.info(f"Drift summary: dataset_drift={drift_summary.get('dataset_drift')}")
        metrics = sorted(
            drift_summary.get("metrics_list", []),
            key=lambda m: m.get("drift_score", 0),
            reverse=True,
        )
        return _html_response(
            request,
            "monitoring.html",
            {
                "drift": drift_summary,
                "metrics": metrics,
                "total_features": len(metrics),
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
    except Exception as e:
        logger.exception("Drift detection failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/json")
def dashboard_json():
    """JSON API for programmatic access to drift results."""
    logger.info("Running drift detection (JSON)")
    try:
        drift_summary = run_drift(output_path=os.getenv("DRIFT_RESULTS_FILE"))
        return JSONResponse(content={"drift_summary": drift_summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("MEDIWATCH_WEBAPP_PORT", "8800")),
        log_level="info",
    )