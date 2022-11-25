from .nginx import NginxMetricAdapters
from .traefik import TraefikMetricAdapters


INGRESS_ADAPTERS = {
    "nginx": NginxMetricAdapters,
    "traefik": TraefikMetricAdapters,
}
