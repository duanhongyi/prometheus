class BaseMetricAdapters(object):

    def __init__(self, request):
        self.request = request

    async def metrics(self):
        pass
