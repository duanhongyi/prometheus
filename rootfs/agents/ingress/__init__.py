import os
from .nginx import NginxIngressCollector
from .traefik import TraefikIngressCollector


INGRESS_COLLECTORS = {
    "k8s.io/ingress-nginx": NginxIngressCollector,
    "traefik.io/ingress-controller": TraefikIngressCollector,
}


def run_agent_forever():
    controller = "traefik.io/ingress-controller"
    ingress_class = os.environ.get("INGRESS_CLASS")
    

    
    Collector = INGRESS_COLLECTORS.get(
        os.environ.get("INGRESS_CLASS"),
        TraefikIngressCollector
    )
    registry = Collector("http://192.168.10.0:8082/metrics").collect()
    os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = 'True'
    from prometheus_client import generate_latest # noqa
    print(generate_latest(registry).decode("utf8"))
