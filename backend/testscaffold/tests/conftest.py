import logging
import os
import pytest
from pyramid import testing


@pytest.fixture(scope="session")
def app_settings():
    from pyramid.paster import get_appsettings

    config_uri = os.environ.get("TESTING_INI")
    settings = get_appsettings(config_uri, name="testscaffold")
    return settings


def _get_session(settings):
    from testscaffold.models import get_engine, get_session_factory

    return get_session_factory(get_engine(settings))()


@pytest.fixture()
def sqla_session(request, app_settings):
    session = _get_session(app_settings)

    def teardown():
        session.rollback()
        # FIXME: needs to be close_all() because close() makes test hang
        # if test fails for some reason
        session.close_all()

    request.addfinalizer(teardown)

    return session


@pytest.fixture()
def minimal_setup(app_settings):
    config = testing.setUp(settings=app_settings)
    config.include("testscaffold.models")
    # make request.user available
    config.add_request_method("testscaffold.util.request:get_user", "user", reify=True)
    config.add_request_method("testscaffold.util.request:safe_json_body", "safe_json_body", reify=True)
    config.add_request_method("testscaffold.util.request:unsafe_json_body", "unsafe_json_body", reify=True)
    config.add_request_method("testscaffold.util.request:get_authomatic", "authomatic", reify=True)


@pytest.fixture()
def base_app(request, app_settings):
    from testscaffold import main
    from webob.multidict import MultiDict
    from pyramid.request import apply_request_extensions

    app = main({}, **app_settings)
    app_request = testing.DummyRequest(base_url="https://testscaffold.com")
    app_request.json_body = None
    app_request.POST = MultiDict()
    app_request.GET = MultiDict()
    app_request.params = MultiDict()
    testing.setUp(registry=app.registry, request=app_request)
    apply_request_extensions(app_request)

    def teardown():
        app_request.tm.abort()
        testing.tearDown()

    request.addfinalizer(teardown)

    return app


@pytest.fixture()
def full_app(request, app_settings):
    from webtest import TestApp
    from testscaffold import main

    app = main({}, **app_settings)
    return TestApp(app)


@pytest.fixture
def with_migrations(app_settings):
    from alembic.config import Config
    from alembic import command
    config_uri = os.environ.get("TESTING_INI")
    alembic_cfg = Config(config_uri)
    alembic_cfg.set_main_option("script_location", "ziggurat_foundations:migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", app_settings["sqlalchemy.url"])
    command.upgrade(alembic_cfg, "head")
    alembic_cfg = Config(config_uri)
    alembic_cfg.set_main_option("script_location", "testscaffold:alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", app_settings["sqlalchemy.url"])
    command.upgrade(alembic_cfg, "head")


def _clean_tables(session):

    from testscaffold.models.meta import Base

    tables = Base.metadata.tables.keys()
    for t in tables:
        if t not in [
            "alembic_ziggurat_foundations_version",
            "alembic_testscaffold_version",
        ]:
            session.execute("truncate %s cascade" % t)
    session.commit()


@pytest.fixture()
def clean_tables(app_settings):
    """ Used to truncate tables per test """
    logging.info("clean_tables")
    session = _get_session(app_settings)
    _clean_tables(session)


@pytest.fixture(scope="class")
def clean_tables_once(app_settings):
    logging.info("clean_tables_once")
    """ Used to truncate tables once per class """
    session = _get_session(app_settings)
    _clean_tables(session)
