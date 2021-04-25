import logging

from ziggurat_foundations.models.base import get_db_session

from testscaffold.models.db import AuthToken

log = logging.getLogger(__name__)


class AuthTokenService:
    @classmethod
    def by_token(cls, token, db_session=None):
        db_session = get_db_session(db_session)
        return db_session.query(AuthToken).filter(AuthToken.token == token).first()
