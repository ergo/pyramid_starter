from __future__ import absolute_import
import logging
from testscaffold.models.auth_token import AuthToken
from ziggurat_foundations.models.base import get_db_session

log = logging.getLogger(__name__)


class AuthTokenService(object):
    @classmethod
    def by_token(cls, token, db_session=None):
        db_session = get_db_session(db_session)
        return db_session.query(AuthToken).filter(
            AuthToken.token == token).first()
