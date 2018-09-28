# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import pytest


@pytest.mark.usefixtures("full_app", "with_migrations", "clean_tables", "sqla_session")
class TestI18N(object):
    def test_default_en_translation(self, full_app):
        url_path = "/"
        response = full_app.get(url_path, {}, status=200)
        assert "Some project name" in response.text
        assert "Register here" in response.text
        assert "Password" in response.text

    def test_pl_translation(self, full_app):
        url_path = "/?_LOCALE_=pl"
        response = full_app.get(url_path, {}, status=200)
        assert "Nazwa projektu" in response.text
        assert "Rejestruj się" in response.text
        assert "Hasło" in response.text
