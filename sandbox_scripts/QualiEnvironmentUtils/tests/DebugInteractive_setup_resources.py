import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from sandbox_scripts.environment.setup.setup_resources import *

dev_helpers.attach_to_cloudshell_as(user="admin", password="dev", domain="Global",
                                    reservation_id="d7be79c2-57d0-4063-9ada-e27cd3c608a7",
                                    server_address="svl-dev-quali")
os.environ["environment_name"] = "Abstract-ALL"

x = EnvironmentSetupResources()
x.execute()
