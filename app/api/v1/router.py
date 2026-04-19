from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    horse_photos,
    horses,
    matches,
    messages,
    notifications,
    search,
    swipes,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(horses.router)
api_router.include_router(horse_photos.router)
api_router.include_router(swipes.router)
api_router.include_router(matches.router)
api_router.include_router(messages.router)
api_router.include_router(notifications.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)
