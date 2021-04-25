import logging

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from testscaffold.services.resource_tree_service import tree_service
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


@view_defaults(route_name="object", permission="view")
class EntriesViews(BaseView):
    @view_config(match_param=("object=entries"), renderer="testscaffold:templates/entry.jinja2")
    def get(self):
        request = self.request
        resource = request.context.resource
        result = tree_service.from_parent_deeper(resource.resource_id, limit_depth=2, db_session=request.dbsession)
        breadcrumbs = tree_service.path_upper(resource.resource_id, db_session=request.dbsession)
        tree = tree_service.build_subtree_strut(result)
        return {
            "resource": resource,
            "breadcrumbs": breadcrumbs,
            "menu_entries": tree["children"],
        }
