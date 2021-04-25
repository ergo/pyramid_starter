import logging

from pyramid.view import view_config, view_defaults

from testscaffold.services.user import UserService
from testscaffold.views import BaseView

log = logging.getLogger(__name__)


@view_defaults(route_name="admin_index", permission="admin_panel")
class AdminPanelView(BaseView):
    @view_config(renderer="testscaffold:templates/admin/index.jinja2")
    def index(self):
        request = self.request
        total_registered_users = UserService.total_count(db_session=request.dbsession)
        latest_logged_user = UserService.latest_logged_user(db_session=request.dbsession)
        latest_registered_user = UserService.latest_registered_user(db_session=request.dbsession)
        return {
            "total_registered_users": total_registered_users,
            "latest_logged_user": latest_logged_user,
            "latest_registered_user": latest_registered_user,
        }
