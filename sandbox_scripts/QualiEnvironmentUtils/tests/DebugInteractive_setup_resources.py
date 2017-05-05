import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from sandbox_scripts.environment.setup.setup_resources import *

dev_helpers.attach_to_cloudshell_as(user="admin", password="admin", domain="Global",
                                    reservation_id="c04d3da4-8025-4efe-9f4d-820ba19d20af",
                                    server_address="localhost")
os.environ["environment_name"] = "Abstract-ALL"

x = EnvironmentSetupResources()
x.execute()
