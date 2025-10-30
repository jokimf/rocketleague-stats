import uvicorn
import replays
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

# import init
import dashboard

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
    return templates.TemplateResponse(request, "upload.html")


@app.post("/rl/uploadreplay")
async def upload_file(request: Request, files: list[UploadFile]):
    # todo auth
    print(files)
    invalid_files = []
    for replay_file in files:
        if not replay_file.filename.endswith(".replay"):
            invalid_files.append(replay_file.filename)
            continue
        try:
            content = await replay_file.read()
            print(content)
            replays.analyze_replay(content)
        except Exception:
            invalid_files.append(replay_file.filename)

    valid = len(invalid_files) == 0
    return {
        "valid": valid,
        "invalid": invalid_files
    }


@app.get("/rl/profile/{player_id}")
async def streaks(request: Request, player_id: int):
    return templates.TemplateResponse(request, "profile.html", d.build_profile_context(int(player_id)))


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

if __name__ == "__main__":
    config = uvicorn.Config("main:app", host="0.0.0.0", port=7823, log_level="warning")
    server = uvicorn.Server(config)
    server.run()
