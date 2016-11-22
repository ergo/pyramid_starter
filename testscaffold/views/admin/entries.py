# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import pyramid.httpexceptions

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from testscaffold.models.entry import Entry
from testscaffold.services.resource_tree_service import tree_service
from testscaffold.util import safe_integer
from testscaffold.validation.forms import (
    EntryCreateForm)
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
        result = tree_service.from_parent_deeper(
            db_session=self.request.dbsession)
        entries_tree = tree_service.build_subtree_strut(result)

        return {'entries_tree': entries_tree}

    @view_config(renderer='testscaffold:templates/admin/entries/edit.jinja2',
                 match_param=('object=entries', 'verb=POST'))
    def post(self):
        request = self.request
        resource_form = EntryCreateForm(
            request.POST, context={'request': request})

        result = tree_service.from_parent_deeper(
            db_session=self.request.dbsession)
        choices = [(0, self.translate(_('Root (/)')))]
        for row in result:
            choices.append((row.Resource.resource_id,
                            '{} {}'.format('-' * row.depth,
                                           row.Resource.resource_name)))

        resource_form.parent_id.choices = choices

        if request.method == "POST" and resource_form.validate():
            resource = Entry()
            parent_id = resource_form.data.get('parent_id') or None
            position = resource_form.data.get('ordering')

            self.shared.populate_instance(resource, resource_form.data,
                                          include_keys=['resource_name',
                                                        'note'])
            resource.parent_id = parent_id
            resource.persist(flush=True, db_session=request.dbsession)

            if position is not None:
                tree_service.set_position(
                    resource_id=resource.resource_id, to_position=position,
                    db_session=self.request.dbsession)
            else:
                # this accounts for the newly inserted row so the total_children
                # will be max+1 position for new row
                total_children = tree_service.count_children(
                    parent_id, db_session=self.request.dbsession)
                tree_service.set_position(
                    resource_id=resource.resource_id,
                    to_position=total_children,
                    db_session=self.request.dbsession)

            log.info('entries_post', extra={
                'type': 'entry',
                'resource_id': resource.resource_id,
                'resource_name': resource.resource_name})
            request.session.flash(
                {'msg': self.translate(_('Entry created.')),
                 'level': 'success'})
            location = request.route_url('admin_objects', object='entries',
                                         verb='GET')
            return pyramid.httpexceptions.HTTPFound(location=location)

        return {"resource_form": resource_form}
