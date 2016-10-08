# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from webhelpers2.html import HTML
from webhelpers2_grid import ObjectGrid


class UsersGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['_numbered', 'user_name', 'email',
                             'registered_date', 'options']
        super(UsersGrid, self).__init__(*args, **kwargs)

        def options_td(col_num, i, item):
            href = self.request.route_url('admin_object', object='users',
                                          object_id=item.id, verb='GET')
            edit_link = HTML.a('Edit', class_='btn btn-info', href=href)
            delete_href = self.request.route_url(
                'admin_object', object='users', object_id=item.id,
                verb='DELETE')
            delete_link = HTML.a(
                'Delete', class_='btn btn-danger', href=delete_href)
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

        def options_td(col_num, i, item):
            href = self.request.route_url(
                'admin_object', object='users', object_id=item.id,
                verb='GET')
            edit_link = HTML.a('Edit', class_='btn btn-info', href=href)
            href = self.request.route_url(
                'admin_object_relation', object='groups',
                object_id=self.additional_kw['group'].id, relation='users',
                verb='DELETE', _query={'user_id': item.id})
            delete_link = HTML.a('Delete', class_='btn btn-danger', href=href)
            return HTML.td(edit_link, ' ', delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class GroupsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['_numbered', 'group_name', 'description',
                             'options']
        super(GroupsGrid, self).__init__(*args, **kwargs)

        def options_td(col_num, i, item):
            edit_href = self.request.route_url(
                'admin_object', object='groups', object_id=item.id,
                verb='GET')
            delete_href = self.request.route_url(
                'admin_object', object='groups', object_id=item.id,
                verb='DELETE')
            edit_link = HTML.a('Edit', class_='btn btn-info', href=edit_href)
            delete_link = HTML.a('Delete', class_='btn btn-danger',
                                 href=delete_href)
            return HTML.td(edit_link, ' ', delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class GroupPermissionsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['perm_name', 'options']
        super(GroupPermissionsGrid, self).__init__(*args, **kwargs)

        def options_td(col_num, i, item):
            href = self.request.route_url(
                    'admin_object_relation', object='groups',
                    object_id=self.additional_kw['group'].id, verb='DELETE',
                    relation='permissions',
                    _query={'permission': item.perm_name})
            delete_link = HTML.a('Delete', class_='btn btn-danger', href=href)
            return HTML.td(delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td


class UserPermissionsGrid(ObjectGrid):
    def __init__(self, *args, **kwargs):
        kwargs['columns'] = ['perm_name', 'options']
        super(UserPermissionsGrid, self).__init__(*args, **kwargs)

        def options_td(col_num, i, item):
            href = self.request.route_url(
                'admin_object_relation', object='users',
                object_id=self.additional_kw['user'].id, verb='DELETE',
                relation='permissions',
                _query={'permission': item.perm_name})
            delete_link = HTML.a('Delete', class_='btn btn-danger', href=href)
            return HTML.td(delete_link,
                           class_='c{}'.format(col_num))

        self.column_formats['options'] = options_td