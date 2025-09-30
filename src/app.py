import uvicorn
from fastapi import FastAPI, Request
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


@app.get("/rl/profile/{player_id}")
async def streaks(request: Request, player_id: int):
    return templates.TemplateResponse(request, "profile.html", d.build_profile_context(int(player_id)))


@app.get("/rl/reload")
async def reload_stats(request: Request):
    d.reload_all_stats()
    return templates.TemplateResponse(request, "index.html", d.build_dashboard_context())

@app.get("/rl/replay/{replay_id}")
async def replay_download(request: Request, replay_id: int):
    return FileResponse(f"./replays/{replay_id}")

if __name__ == "__main__":
    config = uvicorn.Config("main:app", host="0.0.0.0", port=7823, log_level="warning")
    server = uvicorn.Server(config)
    server.run()
