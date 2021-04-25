import zope.sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.orm import configure_mappers
from sqlalchemy.orm import sessionmaker
from ziggurat_foundations import ziggurat_model_init

from testscaffold.models.db import AuthToken  # flake8: noqa
from testscaffold.models.db import Entry  # flake8: noqa
from testscaffold.models.db import ExternalIdentity  # flake8: noqa
from testscaffold.models.db import Group  # flake8: noqa
from testscaffold.models.db import GroupPermission  # flake8: noqa
from testscaffold.models.db import GroupResourcePermission  # flake8: noqa
from testscaffold.models.db import Resource  # flake8: noqa
from testscaffold.models.db import User  # flake8: noqa
from testscaffold.models.db import UserGroup  # flake8: noqa
from testscaffold.models.db import UserPermission  # flake8: noqa
from testscaffold.models.db import UserResourcePermission  # flake8: noqa

ziggurat_model_init(
    User,
    Group,
    UserGroup,
    GroupPermission,
    UserPermission,
    UserResourcePermission,
    GroupResourcePermission,
    Resource,
    ExternalIdentity,
)

# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
configure_mappers()


def get_engine(settings, prefix="sqlalchemy."):
    return engine_from_config(settings, prefix)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
    """
    Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)

    """
    dbsession = session_factory()
    zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def includeme(config):
    """
    Initialize the model for a Pyramid app.

    Activate this setup using ``config.include('testscaffold.models')``.

    """
    settings = config.get_settings()

    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include("pyramid_tm")

    session_factory = get_session_factory(get_engine(settings))
    config.registry["dbsession_factory"] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        "dbsession",
        reify=True,
    )