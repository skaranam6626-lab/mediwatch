from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import encodedValues
import os
from data_preprocessing_scripts.preprocessing import preprocess_data
from models.scripts.trainer import train
from datetime import datetime


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

@app.get("/preprocess", response_class=HTMLResponse)
async def home(request: Request):
    try:
        preprocess_data()
        result={"Status": f"{datetime.now().timestamp()}-preprocessing was run successfully"}
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/train")
async def invokeTrain():
    try:
        train()
        result={"Status": f"{datetime.now().timestamp()}-training was run successfully." }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('PREPROCESSING_TRAINING_MODEL_PORT','8811')), log_level="info")