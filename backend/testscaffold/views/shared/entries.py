# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pyramid.httpexceptions
from pyramid.i18n import TranslationStringFactory

from testscaffold.services.entry import EntryService
from testscaffold.util import safe_integer

ENTRIES_PER_PAGE = 50

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


class EntriesShared:
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request
        self.translate = request.localizer.translate
        self.page = 1

    def collection_list(self, page=1, filter_params=None):
        request = self.request
        entry_paginator = EntryService.get_paginator(
            page=self.page,
            items_per_page=ENTRIES_PER_PAGE,
            # url_maker gets passed to SqlalchemyOrmPage
            url_maker=lambda p: request.current_route_url(_query={"page": p}),
            filter_params=filter_params,
            db_session=request.dbsession,
        )
        return entry_paginator

    def populate_instance(self, instance, data, *args, **kwargs):
        # this is safe and doesn't overwrite entry_password with cleartext
        instance.populate_obj(data, *args, **kwargs)
        log.info(
            "entry_populate_instance", extra={"action": "updated", "entry_id": instance.resource_id},
        )

    def entry_get(self, entry_id):
        request = self.request
        entry = EntryService.get(safe_integer(entry_id), db_session=request.dbsession)
        if not entry:
            raise pyramid.httpexceptions.HTTPNotFound()
        return entry
