from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from pyramid.view import view_config
from pyramid_apispec.helpers import add_pyramid_paths


@view_config(route_name="openapi_spec", renderer="json")
def api_spec(request):
    spec = APISpec(title="Some API", version="1.0.0", openapi_version="2.0", plugins=[MarshmallowPlugin()],)

    # inspect the `foo_route` and generate operations from docstring
    add_pyramid_paths(spec, "api_object", request=request)
    add_pyramid_paths(spec, "api_object_relation", request=request)

    return spec.to_dict()
