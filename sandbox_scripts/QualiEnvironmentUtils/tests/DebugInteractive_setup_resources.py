import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from sandbox_scripts.environment.setup.setup_resources import *

dev_helpers.attach_to_cloudshell_as(user="admin", password="xxx", domain="Global",
                                    reservation_id="3a8cad5c-f197-4b1e-8739-70829957562f",
                                    server_address="svl-dev-quali")

x = EnvironmentSetupResources()
x.execute()
