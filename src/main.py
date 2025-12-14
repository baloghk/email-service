from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()

app = FastAPI(
    title="Email Microservice",
    description="Microservice for sending templated emails via SMTP",
    version="1.0.0"
)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "EmailService",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)