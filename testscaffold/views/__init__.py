from pyramid.security import NO_PERMISSION_REQUIRED


class BaseView(object):
    def __init__(self, request):
        self.request = request
        self.translate = request.localizer.translate


def includeme(config):
    config.scan("testscaffold.views")
    includes = config.registry.settings.get("pyramid.includes", "")
    if "pyramid_debugtoolbar" not in includes:
        config.add_view(
            "testscaffold.views.error_handlers.error",
            context=Exception,
            permission=NO_PERMISSION_REQUIRED,
            renderer="json",
        )
