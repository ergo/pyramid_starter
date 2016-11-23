# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from pyramid.i18n import TranslationStringFactory
from webhelpers2.html import HTML
from webhelpers2_grid import ObjectGrid

_ = TranslationStringFactory('testscaffold')


class UsersGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['_numbered', 'user_name', 'email',
                             'registered_date', 'options']
        super(UsersGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def options_td(col_num, i, item):
            href = self.request.route_url('admin_object', object='users',
                                          object_id=item.id, verb='GET')
            edit_link = HTML.a(
                translate(_('Edit')), class_='btn btn-info', href=href)
            delete_href = self.request.route_url(
                'admin_object', object='users', object_id=item.id,
                verb='DELETE')
            delete_link = HTML.a(
                translate(_('Delete')),
                class_='btn btn-danger',
                href=delete_href)
            return HTML.td(edit_link, ' ', delete_link,
                           class_='c{}'.format(col_num))

        def registered_date_td(col_num, i, item):
            return HTML.td(item.registered_date.strftime('%Y-%m-%d %H:%M'),
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td
        self.column_formats['registered_date'] = registered_date_td


class UsersGroupsGrid(UsersGrid):
    def __init__(self, *args, **kwargs):
        super(UsersGroupsGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def options_td(col_num, i, item):
            href = self.request.route_url(
                'admin_object', object='users', object_id=item.id, verb='GET')
            edit_link = HTML.a(
                translate(_('Edit')), class_='btn btn-info', href=href)
            href = self.request.route_url(
                'admin_object_relation', object='groups',
                object_id=self.additional_kw['group'].id, relation='users',
                verb='DELETE', _query={'user_id': item.id})
            delete_link = HTML.a(
                translate(_('Delete')), class_='btn btn-danger', href=href)
            return HTML.td(edit_link, ' ', delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class GroupsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['_numbered', 'group_name', 'description',
                             'options']
        super(GroupsGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def options_td(col_num, i, item):
            edit_href = self.request.route_url(
                'admin_object', object='groups', object_id=item.id,
                verb='GET')
            delete_href = self.request.route_url(
                'admin_object', object='groups', object_id=item.id,
                verb='DELETE')
            edit_link = HTML.a(
                translate(_('Edit')), class_='btn btn-info', href=edit_href)
            delete_link = HTML.a(
                translate(_('Delete')), class_='btn btn-danger',
                href=delete_href)
            return HTML.td(edit_link, ' ', delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class GroupPermissionsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['perm_name', 'options']
        super(GroupPermissionsGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def options_td(col_num, i, item):
            href = self.request.route_url(
                'admin_object_relation', object='groups',
                object_id=self.additional_kw['group'].id, verb='DELETE',
                relation='permissions',
                _query={'perm_name': item.perm_name})
            delete_link = HTML.a(translate(_('Delete')),
                                 class_='btn btn-danger',
                                 href=href)
            return HTML.td(delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class UserPermissionsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['perm_name', 'options']
        super(UserPermissionsGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def options_td(col_num, i, item):
            href = self.request.route_url(
                'admin_object_relation', object='users',
                object_id=self.additional_kw['user'].id, verb='DELETE',
                relation='permissions',
                _query={'perm_name': item.perm_name})
            delete_link = HTML.a(translate(_('Delete')),
                                 class_='btn btn-danger',
                                 href=href)
            return HTML.td(delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class ResourceUserPermissionsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['user', 'perm_name', 'options']
        super(ResourceUserPermissionsGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def user_td(col_num, i, item):
            return HTML.td(item.user.user_name,
                           class_='c{}'.format(col_num))

        def translate_perm_td(col_num, i, item):
            if getattr(item, 'owner', None) is True:
                perm_name = translate(_('Resource owner'))
            else:
                perm_name = item.perm_name
            return HTML.td(perm_name, class_='c{}'.format(col_num))

        def options_td(col_num, i, item):
            if item.owner is True:
                return HTML.td('', class_='c{}'.format(col_num))

            href = self.request.route_url(
                'admin_object_relation', object='resources',
                object_id=item.resource.resource_id, verb='DELETE',
                relation='user_permissions',
                _query={'perm_name': item.perm_name,
                        'user_name': item.user.user_name})
            delete_link = HTML.a(translate(_('Delete')),
                                 class_='btn btn-danger',
                                 href=href)
            return HTML.td(delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['user'] = user_td
        self.column_formats['perm_name'] = translate_perm_td
        self.column_formats['options'] = options_td


class ResourceGroupPermissionsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['group', 'perm_name', 'options']
        super(ResourceGroupPermissionsGrid, self).__init__(*args, **kwargs)
        translate = self.request.localizer.translate

        def group_td(col_num, i, item):
            return HTML.td(item.group.group_name,
                           class_='c{}'.format(col_num))

        def translate_perm_td(col_num, i, item):
            if getattr(item, 'owner', None) is True:
                perm_name = translate(_('Resource owner'))
            else:
                perm_name = item.perm_name
            return HTML.td(perm_name, class_='c{}'.format(col_num))

        def options_td(col_num, i, item):
            if item.owner is True:
                return HTML.td('', class_='c{}'.format(col_num))

            href = self.request.route_url(
                'admin_object_relation', object='resources',
                object_id=item.resource.resource_id, verb='DELETE',
                relation='group_permissions',
                _query={'perm_name': item.perm_name,
                        'group_id': item.group.id})
            delete_link = HTML.a(translate(_('Delete')),
                                 class_='btn btn-danger',
                                 href=href)
            return HTML.td(delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['group'] = group_td
        self.column_formats['perm_name'] = translate_perm_td
        self.column_formats['options'] = options_td
