import requests
import collections
from prometheus_client import CollectorRegistry, Counter, Gauge
from prometheus_client.core import HistogramMetricFamily
from prometheus_client.parser import text_string_to_metric_families
from .base import BaseIngressCollector


class NginxIngressCollector(BaseIngressCollector):

    def get_traefik_metric(self):
        response = requests.get(self.endpoint)
        yield from text_string_to_metric_families(response.text)

    def parse_open_connections(self, registry, family):
        gauge = Gauge(
            'ingress_open_connections',
            'current number of client connections',
            registry=registry
        )
        for sample in family.samples:
            gauge.inc(sample.value)

    def parse_service_request_duration_seconds(self, registry, family):
        labels, buckets, sum_value, histogram_family = None, None, None, None
        for sample in family.samples:
            if sample.name.endswith("_bucket"):
                if labels is None:
                    labels = {
                        "namespace": sample.labels["namespace"],
                        "service": sample.labels["service"],
                        "method": sample.labels["method"],
                        "status": sample.labels["status"],
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
        Collector = collections.namedtuple("NginxCollector", "collect")
        registry.register(Collector(lambda: [histogram_family]))

    def parse_service_requests(self, registry, family):
        counter = Counter(
            'ingress_service_requests',
            'the total number of client requests',
            ['namespace', 'service', 'status'],
            registry=registry
        )
        for sample in family.samples:
            counter.labels(
                sample.labels["namespace"],
                sample.labels["service"],
                sample.labels["status"],
            ).inc(sample.value)

    def parse_service_requests_bytes(self, registry, family):
        counter = Counter(
            'ingress_service_requests_bytes',
            'the total size for client request',
            ['namespace', 'service', 'method', 'status'],
            registry=registry
        )
        for sample in family.samples:
            if sample.name.endswith("_sum"):
                counter.labels(
                    sample.labels["namespace"],
                    sample.labels["service"],
                    sample.labels["method"],
                    sample.labels["status"],
                ).inc(sample.value)

    def parse_service_responses_bytes(self, registry, family):
        counter = Counter(
            'ingress_service_responses_bytes',
            'the total size for client request',
            ['namespace', 'service', 'method', 'status'],
            registry=registry
        )
        for sample in family.samples:
            if sample.name.endswith("_sum"):
                counter.labels(
                    sample.labels["namespace"],
                    sample.labels["service"],
                    sample.labels["method"],
                    sample.labels["status"],
                ).inc(sample.value)

    def collect(self):
        registry = CollectorRegistry()
        for family in self.hack_get_nginx_metric():
            if (family.name == "nginx_ingress_controller_nginx_process_connections"  # noqa
                    and family.type == "gauge"):
                self.parse_open_connections(registry, family)
            if (family.name == "nginx_ingress_controller_request_duration_seconds"  # noqa
                    and family.type == "histogram"):
                self.parse_service_request_duration_seconds(registry, family)
            if (family.name == "nginx_ingress_controller_requests"
                    and family.type == "counter"):
                self.parse_service_requests(registry, family)
            if (family.name == "nginx_ingress_controller_request_size"
                    and family.type == "histogram"):
                self.parse_service_requests_bytes(registry, family)
            if (family.name == "nginx_ingress_controller_response_size"
                    and family.type == "histogram"):
                self.parse_service_responses_bytes(registry, family)
        return registry
