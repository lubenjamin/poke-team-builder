from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import alerts, changes, counter_team, internal, moves, pokemon, teams

app = FastAPI(title="Pokemon Team Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pokemon.router)
app.include_router(moves.router)
app.include_router(teams.router)
app.include_router(counter_team.router)
app.include_router(alerts.router)
app.include_router(changes.router)
app.include_router(internal.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
