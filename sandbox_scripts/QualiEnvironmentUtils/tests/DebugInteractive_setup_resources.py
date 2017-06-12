import cloudshell.helpers.scripts.cloudshell_dev_helpers as dev_helpers
from sandbox_scripts.environment.setup.setup_resources import *

# change line 155....in helpers to environment_name= os.environ["environmentName"],
os.environ["environmentName"] = "Just1Res"


dev_helpers.attach_to_cloudshell_as(user="admin", password="xxxx", domain="Global",
                                    reservation_id="ad024811-7528-42eb-b2c4-d50003951278",
                                    server_address="svl-dev-quali")

x = EnvironmentSetupResources()
x.execute()
