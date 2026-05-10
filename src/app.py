import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# import init
import dashboard
import utility
from replays import handle_upload
from structs import ReplayError

app = FastAPI()  # Startup: uvicorn app:app --reload --app-dir src
app.mount("/rl/static", StaticFiles(directory="./src/static"), name="static")
templates = Jinja2Templates(directory="./src/templates")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# init.init()
d = dashboard.Dashboard()

@app.get("/")
@app.get("/rl")
async def main(request: Request):
    return templates.TemplateResponse(request, "index.html", d.build_dashboard_context())


@app.get("/rl/records")
async def records(request: Request):
    return templates.TemplateResponse(request, "records.html", d.build_record_context())


@app.get("/rl/games")
async def games(request: Request):
    return templates.TemplateResponse(request, "games.html", d.build_games_context())


@app.get("/rl/upload")
async def upload(request: Request):
    user: utility.User | None = utility.extract_user_info(request)

    if not (user and user.check_credentials() and user.is_premium()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse(request, "upload.html")


@app.post("/rl/uploadreplay", dependencies=[Depends(utility.enforce_max_size)])
async def upload_replay(request: Request, file: UploadFile):
    user: utility.User | None = utility.extract_user_info(request)

    if not (user and user.check_credentials() and user.is_premium()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Exceptions are handled by exception endpoint
    replay: int = handle_upload(file)

    return {"replay_id": replay}


@app.get("/rl/profile/{player_id}")
async def streaks(request: Request, player_id: str):
    return templates.TemplateResponse(request, "profile.html", d.build_profile_context(player_id))


@app.get("/rl/reload")
async def reload_stats(request: Request):
    d.reload_all_stats()
    return templates.TemplateResponse(request, "index.html", d.build_dashboard_context())


@app.get("/rl/replay/{replay_id}")
async def replay_download(request: Request, replay_id: int):
    if not os.path.exists(f"./replays/{replay_id}.replay"):
        raise ReplayError("Replay does not exist.")
    return FileResponse(
        path=f"./replays/{replay_id}.replay",
        media_type="application/octet-stream",
        filename=f"Replay_gameid_{replay_id}.replay"
    )


@app.exception_handler(ReplayError)
async def replay_error_handler(request: Request, exception: ReplayError):
    return JSONResponse(
        status_code=400,
        content={"reason": exception.reason},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exception: Exception):
    logging.error(f"Unexpected error: {str(exception)}")

    return JSONResponse(
        status_code=500,
        content={"reason": "An internal server error occurred."},
    )
