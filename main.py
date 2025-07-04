import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from Routes.modelRoutes import router as model_router
from Routes.userRoutes import router as user_router
from Routes.itemRoutes import router as item_router
import asyncio


app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(model_router)
app.include_router(user_router)
app.include_router(item_router)




