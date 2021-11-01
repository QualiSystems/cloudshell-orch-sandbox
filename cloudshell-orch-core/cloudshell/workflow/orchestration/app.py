from cloudshell.api.cloudshell_api import ConfigParam
from cloudshell.api.cloudshell_api import ReservedResourceInfo
from cloudshell.api.cloudshell_api import ReservationAppResource


class AppResourceRequestInfo(object):
    def __init__(self, app_resource):
        self.app_resource = app_resource
        """:type : ReservationAppResource"""
        self.scripts = {}
        """:type : Dictionary[str,ScriptRequestInfo]"""

    def add_app_config_param(self, script_alias, key, value):
        if script_alias not in self.scripts:
            self.scripts[script_alias] = ScriptRequestInfo(script_alias)
        self.scripts[script_alias].add_script_config_param(key, value)


class ScriptRequestInfo(object):
    def __init__(self, scriptAlias):
        self.scriptAlias = scriptAlias
        """:type : string"""
        self.scriptConfiguration = []
        """:type : list[ConfigParam]"""

    def add_script_config_param(self, key, value):
        self.scriptConfiguration.append(ConfigParam(key, value))


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
