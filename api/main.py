from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import engine, Base
from api.routes.feed import router as feed_router
from api.routes.admin import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(feed_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
