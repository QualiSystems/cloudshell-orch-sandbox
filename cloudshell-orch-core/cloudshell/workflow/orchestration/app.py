from cloudshell.api.cloudshell_api import ConfigParam


class AppResourceRequestInfo(object):
    def __init__(self, app_resource):
        self.app_resource = app_resource
        """:type : ReservationAppResource"""
        self.appConfiguration = []
        """:type : list[ConfigParam]"""

    def add_app_config_param(self, key, value):
        self.appConfiguration.append(ConfigParam(key, value))


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
