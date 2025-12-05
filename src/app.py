import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.config import LOGGING_CONFIG

# import init
import dashboard
import replays
import utility

app = FastAPI()
app.mount("/rl/static", StaticFiles(directory="./src/static"), name="static")
templates = Jinja2Templates(directory="./src/templates")

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
    replay: int = replays.handle_upload(file)

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
    if isinstance(replay_id, int):
        return FileResponse(
            path=f"./replays/{replay_id}.replay",
            media_type="application/octet-stream",
            filename=f"Replay_gameid_{replay_id}.replay"
        )


@app.exception_handler(replays.ReplayError)
async def replay_error_handler(request: Request, exception: replays.ReplayError):
    return JSONResponse(
        status_code=400,
        content={"reason": exception.reason},
    )

if __name__ == "__main__":
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    config = uvicorn.Config("main:app", host="0.0.0.0", port=7823, log_level="warning")
    server = uvicorn.Server(config)
    server.run()
