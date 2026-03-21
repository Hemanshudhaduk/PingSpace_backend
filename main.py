from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
import os

load_dotenv()
from database import Base, engine
import models.user
import models.server
import models.room
import models.message
import models.serveruser
from Routers import chat, auth
import traceback

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,       
    allow_methods=["*"],          
    allow_headers=["*"],
    expose_headers=["*"]           
)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin")
    cors_headers = {}
    if origin:
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "message": exc.detail},
        headers=cors_headers
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    origin = request.headers.get("origin")
    cors_headers = {}
    if origin:
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "message": str(exc)},
        headers=cors_headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    origin = request.headers.get("origin")
    cors_headers = {}
    if origin:
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Validation error"},
        headers=cors_headers
    )

# Create tables for production
try:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print(f"Error creating database tables: {e}")

# Routers
app.include_router(chat.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "PingSpace API is running", "websocket": "/ws/{room_id}"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
