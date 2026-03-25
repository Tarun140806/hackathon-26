from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.decision import router as decision_router
from backend.routes.upload import router as upload_router


app = FastAPI(title="CashClear API", version="0.1.0")

# Allow local frontend dev server to call the API.
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(decision_router)
app.include_router(upload_router)


@app.get("/health")
def health_check() -> dict:
	return {"status": "ok"}
