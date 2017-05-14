from cloudshell.workflow.orchestration.app import App


class Components(object):
    def __init__(self, resources, services, apps):
        self.resources = dict((resource.Name, resource) for resource in resources)
        """:type : dict[str, ReservedResourceInfo]"""
        self.services = dict((service.ServiceName, service) for service in services)
        """:type : dict[str, ServiceInstance]"""
        self.apps = dict((app.Name, App(app)) for app in apps)
        """:type : dict[str, App]"""

    def get_apps_by_name_contains(self, name):
        """
        :param str name:
        :return:
        """
        return [value for key, value in self.apps.iteritems() if name in key]

    def get_resources_by_model(self, model):
        """
        :param str model:
        :return:
        """
        return [value for key, value in self.resources.iteritems() if model == value.ResourceModelName]

    def add_deployed_apps_info(self, sandbox, deployment_results):
        """
        :param Sandbox sandbox:
        :param DeployAppToCloudProviderBulkInfo deployment_results:
        :return:
        """
        reservation_resources = sandbox.automation_api.GetReservationDetails(
            sandbox.id).ReservationDescription.Resources

        self.resources = dict((resource.Name, resource) for resource in reservation_resources)

        if deployment_results is not None:
            for result_item in deployment_results.ResultItems:
                self.apps[result_item.AppName].set_deployed_app_resource(
                    self.resources[result_item.AppDeploymentyInfo.LogicalResourceName])
