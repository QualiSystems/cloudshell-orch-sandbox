from cloudshell.api.cloudshell_api import ConfigParam
from cloudshell.api.cloudshell_api import ReservedResourceInfo
from cloudshell.api.cloudshell_api import ReservationAppResource


class AppResourceRequestInfo(object):
    def __init__(self, app_resource):
        self.app_resource = app_resource
        """:type : ReservationAppResource"""
        self.scripts = {}
        """:type : Dictionary[str,ScriptRequestInfo]"""

    def add_app_config_param(self, alias, key, value):
        if alias not in self.scripts:
            self.scripts[alias] = ScriptRequestInfo(alias)
        self.scripts[alias].add_script_config_param(key, value)


class ScriptRequestInfo(object):
    def __init__(self, alias):
        self.alias = alias
        """:type : string"""
        self.script_configuration = []
        """:type : list[ConfigParam]"""

    def add_script_config_param(self, key, value):
        self.script_configuration.append(ConfigParam(key, value))


class App(object):
    def __init__(self, app_request):
        """
        :type app_request: ReservationAppResource
        """
        self.app_request = AppResourceRequestInfo(app_request)

        """:type : AppResourceRequestInfo"""
        self.deployed_app = None
        """:type : ReservedResourceInfo"""

    def set_deployed_app_resource(self, deployed_app):
        """
        :type deployed_app: ReservedResourceInfo
        """
        self.deployed_app = deployed_app
