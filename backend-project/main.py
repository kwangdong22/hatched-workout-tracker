from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
import models.models  # ensure models are imported
from api.routes import workouts, goals, auth, gamification

app = FastAPI(title="Workout Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Database table auto-creation skipped: {e}")

app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(goals.router)
app.include_router(gamification.router)

@app.get("/health")
def health():
    return {"status": "ok"}
