def get_vm_custom_param(resource_info, param_name):
    """
    :param ResourceInfo resource_info:
    :param param_name:
    :return:
    """
    if isinstance(resource_info.VmDetails, list):
        vm_detail = resource_info.VmDetails[0]
    else:
        vm_detail = resource_info.VmDetails

    for param in vm_detail.VmCustomParams:
        if param.Name == param_name:
            return param

    return None
