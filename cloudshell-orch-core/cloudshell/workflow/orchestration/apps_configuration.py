from cloudshell.api.cloudshell_api import AppConfigurationData, ConfigurationManagementData

from cloudshell.workflow.orchestration.app import App
from cloudshell.workflow.orchestration.setup.default_setup_logic import DefaultSetupLogic


class AppsConfiguration(object):
    def __init__(self, sandbox):
        self.sandbox = sandbox
        """:type : Sandbox"""

    def set_config_param(self, app, alias, key, value):
        """
        :param App app:
        :param str alias:
        :param str key:
        :param str value:
        :return:
        """
        if isinstance(app, App):
            # If deployed in this execution
            if app.app_request.app_resource is not None:
                self.sandbox.components.apps[app.app_request.app_resource.Name].app_request.add_app_config_param(
                    alias, key, value)
                self.sandbox.logger.info(
                    "App config param with key: '{0}' and value: '{1}' was added to app-resource '{2}' at alias '{3}'"
                        .format(key, value, app.app_request.app_resource.Name, alias))

            else:
                self.sandbox.components.apps[app.deployed_app.Name].app_request.add_app_config_param(alias, key,
                                                                                                     value)
                self.sandbox.logger.info(
                    "App config param with key: '{0}' and value: '{1}' was added to app-resource '{2}' at alias '{3}'"
                        .format(key, value, app.deployed_app.Name, alias))

        else:
            self.sandbox.logger.error("set_config_param: app parameter is not from the correct type")
            raise Exception("Sandbox is Active with Errors")

    def apply_apps_configurations(self, apps):
        """
        :param list[App] apps:
        :return:
        """

        if not all(isinstance(app, App) for app in apps):
            self.sandbox.logger.error("apply_apps_configurations should get list of Apps, please refer to the "
                                      "CloudShell DevGuide for more information")
            raise Exception("Sandbox is Active with Errors")

        apps_configuration = []

        for app in apps:
            scripts_configuration = []
            for script in app.app_request.scripts.values():
                scripts_configuration.append(ConfigurationManagementData(
                                               ScriptAlias=script.alias,
                                               ConfigParams=script.script_configuration
                                           ))

            apps_configuration.append(AppConfigurationData(app.deployed_app.Name, scripts_configuration))

            if len(app.app_request.scripts) > 0:
                self.sandbox.logger.debug(
                    "App '{0}' was added to appConfiguration using app request information".format(
                        app.deployed_app.Name))
            else:
                apps_configuration.append(AppConfigurationData(app.deployed_app.Name, []))
                self.sandbox.logger.debug(
                    "App '{0}' was added to appConfiguration without configuration parameters".format(
                        app.deployed_app.Name))

        self.sandbox.logger.info(
            "Configuring apps: {0}".format(
                ', '.join([app_configuration.AppName for app_configuration in apps_configuration])))

        DefaultSetupLogic.configure_apps(api=self.sandbox.automation_api,
                                         reservation_id=self.sandbox.id,
                                         logger=self.sandbox.logger,
                                         appConfigurationsData=apps_configuration)
