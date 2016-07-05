from pyramid.httpexceptions import HTTPBadRequest


def safe_integer(integer):
    try:
        return int(integer)
    except ValueError:
        raise HTTPBadRequest()


def session_provider(request):
    """ provides sqlalchemy session for ziggurat_foundations """
    print(request.dbsession)
    return request.dbsession
