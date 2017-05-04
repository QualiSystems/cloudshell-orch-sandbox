from cloudshell.api.cloudshell_api import AppConfiguration, ConfigParams, ConfigParam, ReservationAppResource


class AppsConfiguration(object):
    def __init__(self, reservation_id, api):
        self.api = api
        """:type : CloudShellAPISession"""
        self.reservation_id = reservation_id
        """:type : str"""
        self.appsConfiguration = []
        """:type : list[AppConfiguration]"""
        self._apps_details_cache = {}
        """:type : dict[str, str]""" # logical resource, app name

    def set_config_param(self, app, key, value):
        """
        :param ReservationAppResource app:
        :param str key:
        :param str value:
        :return:
        """
        self.appsConfiguration.append(AppConfiguration(app.Name, ConfigParams(ConfigParam(key, value))))

    def apply_apps_configurations(self, apps):
        """
        :param list[ReservationAppResource] apps:
        :return:
        """

        #add all apps that doesn't have inputs to appsConfiguration
        for app in apps:
            if app.Name not in [x.AppName for x in self.appsConfiguration]:
                self.appsConfiguration.append(AppConfiguration(app.Name,
                                                               None)) #no config params

        self.api.ConfigureApps(reservationId=self.reservation_id,
                               appConfigurations=self.appsConfiguration)