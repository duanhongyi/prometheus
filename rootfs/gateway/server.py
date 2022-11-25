import sys
import logging
import getopt
import aiohttp
from sanic import Sanic
from .adapters import INGRESS_ADAPTERS


app = Sanic(__name__)
logger = logging.getLogger(__name__)


@app.listener('before_server_start')
def init(app, loop):
    app.ctx.http = aiohttp.ClientSession(loop=loop, auto_decompress=False)


@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(app.ctx.http.close())
    loop.close()


@app.route(
    '/ingresses/<name>/metrics',
    methods=["GET", "HEAD", "OPTIONS"]
)
async def ingress(request, name):
    if name in INGRESS_ADAPTERS:
        adapter = INGRESS_ADAPTERS[name](request)
        await adapter.metrics()
    else:
        await request.respond(status=404)


if __name__ == '__main__':
    options, _ = getopt.getopt(
        sys.argv[1:],
        "h:p:w:",
        ["host=", "port=", "workers="]
    )
    host, port, workers = "0.0.0.0", 8000, 1
    for name, value in options:
        if name in ('-h', '--host'):
            host = value
        elif name in('-p', '--port'):
            port = int(value)
        elif name in('-w', '--workers'):
            workers = int(value)
    app.run(host=host, port=port, workers=workers)
