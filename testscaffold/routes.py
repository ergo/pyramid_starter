# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


def includeme(config):
    config.add_static_view("static", "static", cache_max_age=3600)
    config.add_route("/", "/")
    config.add_route("openapi_spec", "/openapi.json")
    config.add_route("admin_index", "/admin")
    config.add_route("admin_objects", "/admin/{object}/verb/{verb}")
    config.add_route(
        "admin_object",
        "/admin/{object}/{object_id}/verb/{verb}",
        factory="testscaffold.security.object_security_factory",
    )
    config.add_route(
        "admin_object_relation",
        "/admin/{object}/{object_id}/{relation}/verb/{verb}",
        factory="testscaffold.security.object_security_factory",
    )

    config.add_route("register", "/register")
    config.add_route("language", "/language/{language}")
    config.add_route("lost_password", "/lost_password")
    config.add_route("lost_password_generate", "/lost_password_generate")
    config.add_route("social_auth", "/social_auth/{provider}")

    config.add_route("objects", "/{object}/verb/{verb}")
    config.add_route(
        "object",
        "/{object}/{object_id}/verb/{verb}",
        factory="testscaffold.security.object_security_factory",
    )
    config.add_route(
        "object_relation",
        "/{object}/{object_id}/{relation}/verb/{verb}",
        factory="testscaffold.security.object_security_factory",
    )

    config.add_route("api_objects", "/api/{version}/{object}")
    config.add_route(
        "api_object",
        "/api/{version}/{object}/{object_id}",
        factory="testscaffold.security.object_security_factory",
    )
    config.add_route(
        "api_object_relation",
        "/api/{version}/{object}/{object_id}/{relation}",
        factory="testscaffold.security.object_security_factory",
    )
