from prometheus_client import CollectorRegistry


class BaseIngressCollector(object):

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def collect(self) -> CollectorRegistry:
        raise NotImplementedError()
