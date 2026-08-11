from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
from PatientReadmissionPredictor import PatientReadmissionPredictor
import encodedValues

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app=FastAPI()
templates=Jinja2Templates(directory="./webapp/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/predict")
async def predict(request: Request):
    try:
        body_json = await request.json()
        #logger.info(f"{body_json}")
        
        patientRecord={}
        for key, value in body_json.items():
            logger.info(f"ClientAPP: {key}: {value}")   
            modelFeatureName,encodedValue=encodedValues.get_encodedValue(key,value)
            patientRecord[modelFeatureName]=encodedValue
        
        logger.info(f"patientRecord: {patientRecord}")
        result=PatientReadmissionPredictor().predict_patient_readmission(patientRecord)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800, log_level="info")