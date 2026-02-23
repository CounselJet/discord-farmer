"""Simple web server to serve the landing page."""

import os
from aiohttp import web

PORT = int(os.getenv("PORT", 8080))


async def index(_request):
    return web.FileResponse("index.html")


app = web.Application()
app.router.add_get("/", index)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
