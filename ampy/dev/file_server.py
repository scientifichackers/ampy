from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

app = Starlette(debug=True)

@app.route("/{}")
async def root(request):
    return FileResponse()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
