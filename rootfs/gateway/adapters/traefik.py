import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = 'True'

from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest
from prometheus_client.core import (
    Exemplar, HistogramMetricFamily, Timestamp,
)
#from .base import BaseMetricAdapters

class TraefikCollector(object):

    def __init__(self):
        self.collector = []

    def append(self, family):
        self.collector.append(family)

    def collect(self):
        return self.collector


class TraefikMetricAdapters(object):

    def hack_get_traefik_metric(self):
        with open("../traefik.prom") as f:
            from prometheus_client.parser import text_string_to_metric_families
            return text_string_to_metric_families(f.read())

    def get_traefik_metric(self):
        yield from self.hack_get_traefik_metric()

    def parse_open_connections(self, registry, family):
        gauge = Gauge('ingress_open_connections', 'current number of client connections', registry=registry)
        for sample in family.samples:
            gauge.inc(sample.value)

    def parse_service_request_duration_seconds(self, registry, family):
        labels, buckets, sum_value, histogram_family = None, None, None, None
        traefik_collector = TraefikCollector()
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
                histogram_family.add_metric(labels.values(), buckets, sum_value)
                labels, buckets, sum_value  = None, None, None
        traefik_collector.append(histogram_family)
        registry.register(traefik_collector)

    def parse_service_requests(self, registry, family):
        counter = Counter(
            'ingress_service_requests',
            'the total number of client requests',
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

    def metrics(self):
        registry = CollectorRegistry()
        for family in self.get_traefik_metric():
            print(family.name)
            if family.name == "traefik_entrypoint_open_connections":
                self.parse_open_connections(registry, family)
            if family.name == "traefik_service_request_duration_seconds":
                self.parse_service_request_duration_seconds(registry, family)
            if family.name == "traefik_service_requests":
                self.parse_service_requests(registry, family)
            if family.name == "traefik_service_requests_bytes":
                self.parse_service_requests_bytes(registry, family)
            if family.name == "traefik_service_responses_bytes":
                self.parse_service_responses_bytes(registry, family)
        return registry


if __name__ == "__main__":
    registry = TraefikMetricAdapters().metrics()
    print(generate_latest(registry).decode("utf8"))
