from cloudshell.api.cloudshell_api import AppConfiguration

from cloudshell.workflow.orchestration.app import App


class AppsConfiguration(object):
    def __init__(self, sandbox):
        self.sandbox = sandbox
        """:type : Sandbox"""

    def set_config_param(self, app, key, value):
        """
        :param App app:
        :param str key:
        :param str value:
        :return:
        """
        if not isinstance(app, App):
            self.sandbox.components.apps[app.app_request.app_resource.Name].app_request.add_app_config_param(key, value)
            self.sandbox.logger.info("App config param with key: '{0}' and value: '{1}' was added to app-resource '{2}'"
                                     .format(key, value, app.app_request.app_resource.Name))
        else:
            self.sandbox.logger.error("set_config_param: app parameter is not from the correct type")
            raise Exception("Sandbox is Active with Errors")

    def apply_apps_configurations(self, apps):
        """
        :param list[App] apps:
        :return:
        """
        apps_configuration = []

        for app in apps:
            if len(app.app_request.appConfiguration) > 0:
                apps_configuration.append(AppConfiguration(app.deployed_app.Name,
                                                           app.app_request.appConfiguration))
                self.sandbox.logger.debug(
                    "App '{0}' was added to appConfiguration using app request information".format(
                        app.deployed_app.Name))


            else:
                apps_configuration.append(AppConfiguration(app.deployed_app.Name, None))
                self.sandbox.logger.debug(
                    "App '{0}' was added to appConfiguration without configuration parameters".format(
                        app.deployed_app.Name))

        self.sandbox.logger.info(
            "Configuring apps: {0}".format(', '.join([app_configuration.AppName for app_configuration in apps_configuration])))

        self.sandbox.automation_api.ConfigureApps(reservationId=self.sandbox.reservation_id,
                                                  appConfigurations=apps_configuration)
