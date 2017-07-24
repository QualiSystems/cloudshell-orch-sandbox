from cloudshell.api.cloudshell_api import AppInfo, ResourceInfoVmDetails, ReservedResourceInfo, ServiceInstance
from cloudshell.workflow.orchestration.app import App


class Components(object):
    def __init__(self, resources, services, apps):
        self.apps = {app.Name : App(app)) for app in apps if len(app.DeploymentPaths) > 0}  # avoid bug in
        # cloudshell-automation-api where an app named None returns even when there are no apps in the reservation
        """:type : dict[str, App]"""
        self.resources = {}
        """:type : dict[str, ReservedResourceInfo]"""
        self.services = dict((service.Alias, service) for service in services)
        """:type : dict[str, ServiceInstance]"""

        for resource in resources:
            if isinstance(resource.VmDetails, ResourceInfoVmDetails):  ##if deployed app or static VM
                self.apps[resource.Name] = App(None)
                self.apps[resource.Name].set_deployed_app_resource(resource)
            else:
                self.resources[resource.Name] = resource

    def get_apps_by_name_contains(self, name):
        """
        :param str name:
        :rtype: list[App]
        """
        return [value for key, value in self.apps.iteritems() if name in key]

    def get_resources_by_model(self, model):
        """
        :param str model:
        :rtype: list[ReservedResourceInfo]
        """
        return [value for key, value in self.resources.iteritems() if model == value.ResourceModelName]

    def get_services_by_alias(self, alias):
        """
        :param str alias:
        :rtype: list[ServiceInstance]
        """
        return [value for key, value in self.services.iteritems() if alias == value.Alias]

    def get_services_by_name(self, name):
        """
        :param str name:
        :rtype: list[ServiceInstance]
        """
        return [value for key, value in self.services.iteritems() if name == value.ServiceName]

    def refresh_components(self, sandbox):
        """
        :param Sandbox sandbox: 
        :return:
        """
        reservation_description = sandbox.automation_api.GetReservationDetails(
            sandbox.id).ReservationDescription

        self.resources = dict((resource.Name, resource) for resource in reservation_description.Resources)
        self.services = dict((service.Alias, service) for service in reservation_description.Services)

        if reservation_description.Apps is not None:
            for app in reservation_description.Apps:
                if (app.Name not in self.apps.keys() and
                            len(app.DeploymentPaths) > 0):
                    # to avoid bug in cloudshell-automation-api where an app named None returns even when
                    # there are no apps in the reservation
                    self.apps[app.Name] = App(app)

        if self.resources is not None:
            for resource_name, resource in self.resources.iteritems():
                if isinstance(resource.AppDetails, AppInfo):  # if deployed app but not static VM
                    if resource.AppDetails.AppName in self.apps:
                        self.apps[resource.AppDetails.AppName].set_deployed_app_resource(resource)
