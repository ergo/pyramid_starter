# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import pyramid.httpexceptions

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from testscaffold.grids import UsersGrid, UserPermissionsGrid
from testscaffold.models.user import User
from testscaffold.util import safe_integer
from testscaffold.validation.forms import (
    UserAdminCreateForm,
    UserAdminUpdateForm,
    DirectPermissionForm)
from testscaffold.views.shared.entries import ENTRIES_PER_PAGE, EntriesShared
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


@view_defaults(route_name='admin_objects', permission='admin_entries')
class AdminEntriesViews(BaseView):
    def __init__(self, request):
        super(AdminEntriesViews, self).__init__(request)
        self.shared = EntriesShared(request)

    @view_config(renderer='testscaffold:templates/admin/entries/index.jinja2',
                 match_param=('object=entries', 'verb=GET'))
    def collection_list(self):
        page = safe_integer(self.request.GET.get('page', 1))
        entries_paginator = self.shared.collection_list(page=page)
        start_number = (ENTRIES_PER_PAGE * (self.shared.page - 1) + 1) or 1
        # entries_grid = UsersGrid(entries_paginator,
        #                          start_number=start_number,
        #                          request=self.request)
        entries_grid = None

        return {'entries_paginator': entries_paginator,
                'entries_grid': entries_grid}

    @view_config(renderer='testscaffold:templates/admin/entries/edit.jinja2',
                 match_param=('object=entries', 'verb=POST'))
    def post(self):
        request = self.request
        return {}