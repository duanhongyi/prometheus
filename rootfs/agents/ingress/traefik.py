import requests
import collections
from prometheus_client import CollectorRegistry, Counter, Gauge
from prometheus_client.core import HistogramMetricFamily
from prometheus_client.parser import text_string_to_metric_families

from .base import BaseIngressCollector


class TraefikIngressCollector(BaseIngressCollector):

    def get_traefik_metric(self):
        response = requests.get(self.endpoint)
        yield from text_string_to_metric_families(response.text)

    def parse_open_connections(self, registry, family):
        gauge = Gauge(
            'ingress_open_connections',
            'current number of client connections',
            registry=registry)
        for sample in family.samples:
            gauge.inc(sample.value)

    def parse_service_request_duration_seconds(self, registry, family):
        labels, buckets, sum_value, histogram_family = None, None, None, None
        for sample in family.samples:
            if sample.name.endswith("_bucket"):
                if labels is None:
                    service = sample.labels["service"]
                    labels = {
                        "namespace": service.split("-")[0],
                        "service": "-".join(service.split("-")[1:-1]),
                        "method": sample.labels["method"],
                        "status": sample.labels["code"],
                    }
                if buckets is None:
                    buckets = []
                buckets.append((sample.labels['le'], sample.value))
            elif sample.name.endswith("_sum"):
                sum_value = sample.value
            elif sample.name.endswith("_count"):
                if histogram_family is None:
                    histogram_family = HistogramMetricFamily(
                        'ingress_service_request_duration_seconds',
                        'the request processing time in milliseconds.',
                        labels=labels
                    )
                histogram_family.add_metric(
                    labels.values(), buckets, sum_value)
                labels, buckets, sum_value = None, None, None
        Collector = collections.namedtuple("TraefikCollector", "collect")
        registry.register(Collector(lambda: [histogram_family]))

    def parse_service_requests(self, registry, family):
        counter = Counter(
            'ingress_service_requests',
            'the total number of client requests',
            ['namespace', 'service', 'status'],
            registry=registry
        )
        for sample in family.samples:
            service = sample.labels["service"]
            counter.labels(
                service.split("-")[0],
                "-".join(service.split("-")[1:-1]),
                sample.labels["code"]
            ).inc(sample.value)

    def parse_service_requests_bytes(self, registry, family):
        counter = Counter(
            'ingress_service_requests_bytes',
            'the total size for client request',
            ['namespace', 'service', 'method', 'status'],
            registry=registry
        )
        for sample in family.samples:
            service = sample.labels["service"]
            counter.labels(
                service.split("-")[0],
                "-".join(service.split("-")[1:-1]),
                sample.labels["method"],
                sample.labels["code"]
            ).inc(sample.value)

    def parse_service_responses_bytes(self, registry, family):
        counter = Counter(
            'ingress_service_responses_bytes',
            'the total size for client request',
            ['namespace', 'service', 'method', 'status'],
            registry=registry
        )
        for sample in family.samples:
            service = sample.labels["service"]
            counter.labels(
                service.split("-")[0],
                "-".join(service.split("-")[1:-1]),
                sample.labels["method"],
                sample.labels["code"]
            ).inc(sample.value)

    def collect(self):
        registry = CollectorRegistry()
        for family in self.get_traefik_metric():
            if (family.name == "traefik_entrypoint_open_connections"
                    and family.type == "gauge"):
                self.parse_open_connections(registry, family)
            if (family.name == "traefik_service_request_duration_seconds"
                    and family.type == "histogram"):
                self.parse_service_request_duration_seconds(registry, family)
            if (family.name == "traefik_service_requests"
                    and family.type == "counter"):
                self.parse_service_requests(registry, family)
            if (family.name == "traefik_service_requests_bytes"
                    and family.type == "counter"):
                self.parse_service_requests_bytes(registry, family)
            if (family.name == "traefik_service_responses_bytes"
                    and family.type == "counter"):
                self.parse_service_responses_bytes(registry, family)
        return registry
