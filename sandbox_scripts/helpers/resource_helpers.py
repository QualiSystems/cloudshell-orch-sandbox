def get_vm_custom_param(resource_info, param_name):
    """
    :param ResourceInfo resource_info:
    :param param_name:
    :return:
    """
    vm_detail = get_vm_details(resource_info)

    for param in vm_detail.VmCustomParams:
        if param.Name == param_name:
            return param

    return None


def get_vm_details(resource_info):
    """
    :param ResourceInfo resource_info:
    :return:
    :rtype:
    """
    if isinstance(resource_info.VmDetails, list):
        vm_detail = resource_info.VmDetails[0]
    else:
        vm_detail = resource_info.VmDetails
    return vm_detail


def is_deployed_app_or_descendant_of_deployed_app(resource, cached_resources):
    """
    :param ResourceInfo resource:
    :param cached_resources:
    :return:
    :rtype boolean:
    """
    deployed_app_name = resource.Name.split('/')[0]
    vm_details = get_vm_details(cached_resources[deployed_app_name])
    return hasattr(vm_details, "UID")


def get_resources_created_in_res(reservation_details, reservation_id):
    """
    :param GetReservationDescriptionResponseInfo reservation_details:
    :param str reservation_id:
    :return:
    """
    resources = filter(
            lambda x: x.CreatedInReservation and x.CreatedInReservation.lower() == reservation_id.lower(),
            reservation_details.ReservationDescription.Resources)
    return resources


def find_resource_by_name(reservation_details, resource_name):
    """
    :param GetReservationDescriptionResponseInfo reservation_details:
    :param str resource_name:
    :return:
    :rtype ReservedResourceInfo:
    """
    resource_name = resource_name.lower()

    resources = filter(lambda x: x.Name.lower() == resource_name, reservation_details.ReservationDescription.Resources)
    if len(resources) > 0:
        return resources[0]
    return None


def get_root(resource_name):
    return resource_name.lower().split('/')[0]
