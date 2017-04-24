import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
import os
from sandbox_scripts.environment.teardown.teardown_resources import *

dev_helpers.attach_to_cloudshell_as(user="admin", password="dev", domain="Global",
                                    reservation_id="3e43b3b8-9f5a-45d9-a820-4ce471cb8e07",
                                    server_address="svl-dev-quali")
os.environ["environment_name"] = "Abstract-ALL"

x = EnvironmentTeardownResources()
x.execute()
