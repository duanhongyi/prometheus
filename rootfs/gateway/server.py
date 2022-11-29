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
    """
    # HELP ingress_open_connections current number of client connections.
    # TYPE ingress_open_connections gauge
    ingress_open_connections 1
    # HELP ingress_service_request_duration_seconds The request processing time in milliseconds.
    # TYPE ingress_service_request_duration_seconds histogram
    ingress_service_request_duration_seconds_bucket{namespace="drycc",service="drycc-grafana",method="GET",status="200",le="0.1"} 1
    ingress_service_request_duration_seconds_sum{namespace="drycc",service="drycc-grafana",method="GET",status="200"} 1
    ingress_service_request_duration_seconds_count{namespace="drycc",service="drycc-grafana",method="GET",status="200"} 1
    # 
    ingress_service_requests_total{namespace="drycc",service="drycc-grafana",method="GET",status="200"} 1

    ingress_service_requests_bytes_total{namespace="drycc",service="drycc-grafana",method="GET",status="200"} 1

    ingress_service_responses_bytes_total{namespace="drycc",service="drycc-grafana",method="GET",status="200"} 1
    """
    if name in INGRESS_ADAPTERS:
        adapter = INGRESS_ADAPTERS[name](app, request)
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
