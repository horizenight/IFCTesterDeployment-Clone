from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import tempfile
import time
import ifctester
import ifctester.reporter
import ifcopenshell

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "API is live",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0", 
        "idsSchemaVersion": "//TODO"
    }

# API router for /api/ids
@app.post("/api/ids/loadIds")
async def loadIds(ids_file: UploadFile = File(...)):
    tmp_file_path = None
    output_file_path = None

    if not ids_file.filename.endswith(".ids"):
        raise HTTPException(status_code=400, detail="Invalid file extension. Only .ids files are allowed.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ids") as tmp_file:
            tmp_file.write(await ids_file.read())
            tmp_file.flush()
            tmp_file_path = tmp_file.name

        ids_data = ifctester.ids.open(tmp_file_path, validate=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as output_file:
            output_file_path = output_file.name
            is_valid = ids_data.to_xml(output_file_path)

        with open(output_file_path, 'r') as xml_file:
            output_xml_content = xml_file.read()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid .ids file cannot be loaded Error: {str(e)}")

    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        if output_file_path and os.path.exists(output_file_path):
            os.remove(output_file_path)

    return {
        "xml": output_xml_content,
        "is_valid": is_valid
    }

@app.post("/api/ids/auditIds")
async def auditIds(ids_file: UploadFile = File(...), ifc_file: UploadFile = File(...)):
    ids_temp = tempfile.NamedTemporaryFile(delete=False)
    ifc_temp = tempfile.NamedTemporaryFile(delete=False)

    try:
        ids_temp.write(await ids_file.read())
        ifc_temp.write(await ifc_file.read())

        ids_temp.close()
        ifc_temp.close()

        start = time.time()
        ids_data = ifctester.ids.open(ids_temp.name)
        ifc_data = ifcopenshell.open(ifc_temp.name)
        print("Finished loading:", time.time() - start)
        start = time.time()
        ids_data.validate(ifc_data)
        print("Finished validating:", time.time() - start)

        start = time.time()
        engine = ifctester.reporter.Json(ids_data)
        engine.report()
        ifctester.reporter.Console(ids_data).report()
   
        print("Finished reporting:", time.time() - start)
        return {
            "content": engine.to_string()
        }
    
    finally:
        os.remove(ids_temp.name)
        os.remove(ifc_temp.name)
