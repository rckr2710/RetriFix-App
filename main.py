from fastapi import FastAPI
from database import Base, engine
from routers import auth, chat

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Base.metadata.drop_all(bind=engine)
    # init_db()
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(chat.router)

