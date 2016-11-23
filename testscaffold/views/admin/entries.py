# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import pyramid.httpexceptions

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from ziggurat_foundations import noop
from ziggurat_foundations.permissions import ANY_PERMISSION
from ziggurat_foundations.models.services.resource import ResourceService

from testscaffold.models.entry import Entry
from testscaffold.services.resource_tree_service import tree_service
from testscaffold.util import safe_integer
from testscaffold.validation.forms import (
    ResourcePermissionForm,
    EntryCreateForm
)
from testscaffold.grids import ResourceUserPermissionsGrid

from testscaffold.views.shared.entries import ENTRIES_PER_PAGE, EntriesShared
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


def get_possible_parents(request):
    result = tree_service.from_parent_deeper(
        db_session=request.dbsession)

    choices = [('', request.localizer.translate(_('Root (/)')))]
    for row in result:
        choices.append((row.Resource.resource_id,
                        '{} {}'.format('--' * row.depth,
                                       row.Resource.resource_name)))
    return choices


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
        choices = get_possible_parents(self.request)
        resource_form.parent_id.choices = choices

        if request.method == "POST" and resource_form.validate():
            resource = Entry()
            position = resource_form.data.get('ordering')
            self.shared.populate_instance(resource, resource_form.data,
                                          exclude_keys=['ordering'])
            request.user.resources.append(resource)
            resource.persist(flush=True, db_session=request.dbsession)

            if position is not None:
                tree_service.set_position(
                    resource_id=resource.resource_id, to_position=position,
                    db_session=self.request.dbsession)
            else:
                # this accounts for the newly inserted row so the total_children
                # will be max+1 position for new row
                total_children = tree_service.count_children(
                    resource.parent_id, db_session=self.request.dbsession)
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


@view_defaults(route_name='admin_object', permission='admin_users')
class AdminEntryViews(BaseView):
    def __init__(self, request):
        super(AdminEntryViews, self).__init__(request)
        self.shared = EntriesShared(request)

    @view_config(renderer='testscaffold:templates/admin/entries/edit.jinja2',
                 match_param=('object=entries', 'verb=GET'))
    @view_config(renderer='testscaffold:templates/admin/entries/edit.jinja2',
                 match_param=('object=entries', 'verb=PATCH'))
    def get_patch(self):
        request = self.request
        resource = self.request.context.resource

        breadcrumbs = tree_service.path_upper(
            resource.resource_id, db_session=self.request.dbsession)

        permission_form = ResourcePermissionForm(
            request.POST, context={'request': request})
        choices = [(p, p) for p in resource.__possible_permissions__]
        permission_form.perm_name.choices = choices

        permissions = ResourceService.users_for_perm(
            resource, perm_name=ANY_PERMISSION, skip_group_perms=True)

        permissions_grid = ResourceUserPermissionsGrid(
            permissions, request=request)

        choices = get_possible_parents(self.request)
        resource_form = EntryCreateForm(
            request.POST, obj=resource,
            context={'request': request, 'modified_obj': resource})
        resource_form.parent_id.choices = choices

        if request.method == "POST" and resource_form.validate():
            parent_id = resource_form.data.get('parent_id', noop)
            position = resource_form.data.get('ordering', noop)
            # we need to not change_parent_id or order of element
            # to not confuse tree manager
            self.shared.populate_instance(resource, resource_form.data,
                                          exclude_keys=['parent_id',
                                                        'ordering'])
            into_new_parent = parent_id != resource.parent_id and \
                              parent_id is not noop
            if position is not noop or into_new_parent:
                if not position and into_new_parent:
                    position = tree_service.count_children(
                        parent_id, db_session=self.request.dbsession) + 1
                tree_service.move_to_position(
                    resource_id=resource.resource_id, new_parent_id=parent_id,
                    to_position=position, db_session=self.request.dbsession)

        return {"breadcrumbs": breadcrumbs,
                "resource": resource,
                "resource_form": resource_form,
                "permission_form": permission_form,
                "permissions_grid": permissions_grid}
