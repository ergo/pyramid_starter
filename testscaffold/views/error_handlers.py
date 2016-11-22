from pyramid.view import view_config
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.renderers import render_to_response


@view_config(context='testscaffold.exceptions.JSONException',
             permission=NO_PERMISSION_REQUIRED, renderer='json')
def invalid_json(context, request):
    request.response.status = 422
    return 'Incorrect JSON'


@view_config(context='marshmallow.ValidationError',
             permission=NO_PERMISSION_REQUIRED,
             renderer='json')
def marshmallow_invalid_data(context, request):
    request.response.status = 422
    return context.messages


@view_config(context='passlib.exc.MissingBackendError',
             permission=NO_PERMISSION_REQUIRED,
             renderer='string')
def no_bcrypt_found(context, request):
    request.response.status = 500
    return str(context)


@view_config(context='pyramid.exceptions.HTTPForbidden',
             permission=NO_PERMISSION_REQUIRED,
             renderer='string')
def forbidden(context, request):
    request.response.status = 403
    if request.matched_route and request.matched_route.name.startswith('api_'):
        return 'FORBIDDEN'
    return render_to_response(
        'testscaffold:templates/error_handlers/forbidden.jinja2', value={},
        request=request)


def error(context, request):
    request.response.status = 500
    if request.matched_route and request.matched_route.name.startswith('api_'):
        return 'EXCEPTION'
    return render_to_response(
        'testscaffold:templates/error_handlers/error.jinja2', value={},
        request=request)