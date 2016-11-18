class BaseView(object):
    def __init__(self, request):
        self.request = request
        self.translate = request.localizer.translate
