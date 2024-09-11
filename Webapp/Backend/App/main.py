from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from APP.IDS.ids import router as ids_router

app = FastAPI()

app.include_router(ids_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.get("/")
async def root():
    return {
        "status": "API is live",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0", 
        "idsSchemaVersion": "//TODO"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)