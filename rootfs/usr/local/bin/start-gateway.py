import sys
import logging
import getopt
from sanic import Sanic


app = Sanic(__name__)
logger = logging.getLogger(__name__)


def nginx_exproter_paster():
    pass


def traefik_exproter_paster():
    pass


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
    waiting_for_backends()
    app.add_task(check_health_task)
    app.run(host=host, port=port, workers=workers)
