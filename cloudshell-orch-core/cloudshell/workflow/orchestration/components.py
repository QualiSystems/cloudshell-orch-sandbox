from cloudshell.api.cloudshell_api import ReservedResourceInfo, ServiceInstance, ReservationAppResource


class Components(object):
    def __init__(self, resources, services, apps):
        self.resources = dict((resource.Name, resource) for resource in resources)
        """:type : dict[str, ReservedResourceInfo]"""
        self.services = dict((service.ServiceName, service) for service in services)
        """:type : dict[str, ServiceInstance]"""
        self.apps = dict((app.Name, app) for app in apps)
        """:type : dict[str, ReservationAppResource]"""

    def get_apps_by_name_contains(self, name):
        results = []
        for key, value in self.apps.iteritems():
            if name in key:
                results.append(value)
        return results

    def get_resources_by_model(self, model):
        return [x for x in self.resources if model == x.ResourceModelName]

    def add_app_deployment_results(self, sandbox, deployment_results):
        """
        :param Sandbox sandbox:
        :param DeployAppToCloudProviderBulkInfo deployment_results:
        :return:
        """
        for deployment_result in deployment_results:
            logical_resource = deployment_result.AppDeploymentyInfo.LogicalResourceName
            sandbox.apps_configuration._apps_details_cache[logical_resource]=deployment_result[deployment_result.AppName]
        pass
