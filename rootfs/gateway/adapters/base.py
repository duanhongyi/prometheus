class BaseMetricAdapters(object):

    def __init__(self, app, request):
        self.app = app
        self.request = request

    async def metrics(self):
        raise NotImplementedError()
