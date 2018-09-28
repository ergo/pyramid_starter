# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import sqlalchemy.types as types

import testscaffold.util.encryption as encryption


class EncryptedUnicode(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if not value:
            return value
        return encryption.encrypt_fernet(value.encode("utf8"))

    def process_result_value(self, value, dialect):
        if not value:
            return value
        return encryption.decrypt_fernet(value).decode("utf8")
