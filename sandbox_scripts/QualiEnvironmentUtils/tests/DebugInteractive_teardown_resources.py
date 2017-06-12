import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from sandbox_scripts.environment.teardown.teardown_resources import *
import os


os.environ["environmentName"] = "Just1Res"

dev_helpers.attach_to_cloudshell_as(user="admin", password="xxxx", domain="Global",
                                    reservation_id="2bc2e45f-63e6-41cb-a8f5-fe34e042a75e",
                                    server_address="svl-dev-quali")

x = EnvironmentTeardownResources()
x.execute()
