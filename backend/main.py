from fastapi import FastAPI

app = FastAPI(title="DevConnect API")


@app.get("/health")
def health():
    return {"status": "ok"}


# Routers will be included here once implemented, e.g.:
# from routes import users, matching, reports
# app.include_router(users.router)
# app.include_router(matching.router)
# app.include_router(reports.router)
