from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes import users, matching

app = FastAPI(title="DevConnect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Dev convenience only — use Alembic migrations for real schema changes.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(matching.router)
# Reports router (Phase 9) lands here once written:
# from routes import reports
# app.include_router(reports.router)
