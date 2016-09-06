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
    :rtype: VmDetail
    """
    if isinstance(resource_info.VmDetails, list):
        vm_detail = resource_info.VmDetails[0]
    else:
        vm_detail = resource_info.VmDetails
    return vm_detail
