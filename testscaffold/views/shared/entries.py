# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from testscaffold.util import safe_integer

from testscaffold.services.entry import EntryService

ENTRIES_PER_PAGE = 50

log = logging.getLogger(__name__)


class EntriesShared(object):
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request
        self.page = None

    def collection_list(self):
        request = self.request
        self.page = safe_integer(request.GET.get('page', 1))
        filter_params = request.GET.mixed()
        entry_paginator = EntryService.get_paginator(
            page=self.page,
            items_per_page=ENTRIES_PER_PAGE,
            # url_maker gets passed to SqlalchemyOrmPage
            url_maker=lambda p: request.current_route_url(_query={"page": p}),
            filter_params=filter_params,
            db_session=request.dbsession
        )
        return entry_paginator

    def populate_instance(self, instance, data):
        # this is safe and doesn't overwrite entry_password with cleartext
        instance.populate_obj(data)
        log.info('entry_populate_instance',
                 extra={'action': 'updated', 'entry_id': instance.resource_id})

    def delete(self, instance):
        log.info('entry_delete', extra={'entry_id': instance.id,
                                        'entry_name': instance.entry_name})
        instance.delete(self.request.dbsession)
        self.request.session.flash({'msg': 'Entry removed.',
                                    'level': 'success'})
