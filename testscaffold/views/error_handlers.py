from pyramid.view import view_config
from pyramid.security import NO_PERMISSION_REQUIRED


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
