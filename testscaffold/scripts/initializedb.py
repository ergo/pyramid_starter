import os
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from testscaffold.models.meta import Base
from testscaffold.models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )

from testscaffold.models.user import User
from testscaffold.models.group import Group
from testscaffold.models.group_permission import GroupPermission


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, name='testscaffold',
                               options=options)

    engine = get_engine(settings)

    session_factory = get_session_factory(engine)
    dbsession = get_tm_session(session_factory, transaction.manager)

    with transaction.manager:
        user = User(user_name="admin", email='foo@localhost')
        user.set_password('admin')
        admin_object = Group(group_name='Administrators')
        group_permission = GroupPermission(perm_name='root_administration')
        dbsession.add(admin_object)
        admin_object.permissions.append(group_permission)
        admin_object.users.append(user)

        test_group = Group(group_name='Other group')
        dbsession.add(test_group)
        for x in range(1, 25):
            user = User(user_name="test{}".format(x),
                        email='foo{}@localhost'.format(x))
            user.set_password('test')
            test_group.users.append(user)
