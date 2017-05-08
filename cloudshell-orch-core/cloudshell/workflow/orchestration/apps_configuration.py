from cloudshell.api.cloudshell_api import AppConfiguration, ConfigParams, ConfigParam, ReservationAppResource
from logging import Logger


class AppsConfiguration(object):
    def __init__(self, reservation_id, api, logger):
        self.api = api
        """:type : CloudShellAPISession"""
        self.reservation_id = reservation_id
        """:type : str"""
        self.appsConfiguration = []
        """:type : list[AppConfiguration]"""
        self._apps_details_cache = {}
        """:type : dict[str, str]"""  # logical resource, app name
        self.logger = logger
        """:type : logging.Logger"""

    def set_config_param(self, deployed_app, key, value):
        """
        :param ReservedResourceInfo deployed_app:
        :param str key:
        :param str value:
        :return:
        """
        self.appsConfiguration.append(AppConfiguration(deployed_app.Name, ConfigParams(ConfigParam(key, value))))
        self.logger.debug("App config param with key: {0} and value: {1} was added to app-resource {2}"
                          .format(key, value, deployed_app.Name))

    def apply_apps_configurations(self, deployed_apps):
        """
        :param list[ReservedResourceInfo] deployed_apps:
        :return:
        """

        # add all apps that doesn't have inputs to appsConfiguration
        for deployed_app in deployed_apps:
            if deployed_app.Name not in [x.AppName for x in self.appsConfiguration]:
                self.appsConfiguration.append(AppConfiguration(deployed_app.Name,
                                                               None))  # no config params


        self.api.ConfigureApps(reservationId=self.reservation_id,
                               appConfigurations=self.appsConfiguration)
