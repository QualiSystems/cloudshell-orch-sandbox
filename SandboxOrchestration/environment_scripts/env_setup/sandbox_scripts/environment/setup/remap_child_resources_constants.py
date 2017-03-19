TARGET_TYPE_RESOURCE = 'Resource'
REMAP_CHILD_RESOURCES = 'connect_child_resources'
MISSING_COMMAND_ERROR = '101'


def remap_child_resources(api, deployed_app_name, sandbox_id):
        # for devices that are autoloaded and have child resources attempt to call "Connect child resources"
        # which copies CVCs from app to deployed app ports.
        api.ExecuteCommand(sandbox_id, deployed_app_name,
                           TARGET_TYPE_RESOURCE,
                           REMAP_CHILD_RESOURCES, [])
