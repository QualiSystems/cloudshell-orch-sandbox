import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from sandbox_scripts.environment.teardown.teardown_resources import *

dev_helpers.attach_to_cloudshell_as(user="admin", password="xx", domain="Global",
                                    reservation_id="bc0517e5-7240-4184-b04d-19e755f9c9a7",
                                    server_address="svl-dev-quali")

x = EnvironmentTeardownResources()
x.execute()
