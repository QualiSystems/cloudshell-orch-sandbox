from cloudshell.api.cloudshell_api import ReservedResourceInfo, ServiceInstance, ReservationAppResource


class Components(object):
    def __init__(self, resources, services, apps):
        self.Resources = dict((resource.Name, resource) for resource in resources)
        """:type : dict[str, ReservedResourceInfo]"""
        self.Services = dict((service.ServiceName, service) for service in services)
        """:type : dict[str, ServiceInstance]"""
        self.Apps = dict((app.Name, app) for app in apps)
        """:type : dict[str, ReservationAppResource]"""

    def get_apps_by_name_contains(self, name):
        return [x for x in self.Apps if name in x]