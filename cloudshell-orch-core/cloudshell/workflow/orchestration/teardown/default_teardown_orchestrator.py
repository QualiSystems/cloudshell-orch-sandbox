from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_logic import DefaultTeardownLogic


class DefaultTeardownWorkflow(object):
    def __init__(self):
        pass

    def register(self, sandbox):
        """
        :param Sandbox sandbox:
        :return:
        """
        sandbox.logger.info("Adding default teardown orchestration")
        sandbox.workflow.add_to_teardown(self.default_teardown, None)

    def default_teardown(self, sandbox, components):
        """
        :param Sandbox sandbox:
        :return:
        """
        api = sandbox.automation_api
        reservation_details = api.GetReservationDetails(sandbox.id)

        api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                            message='Beginning sandbox teardown')

        DefaultTeardownLogic.disconnect_all_routes_in_reservation(api=api,
                                                                  reservation_details=reservation_details,
                                                                  reservation_id= sandbox.id,
                                                                  logger=sandbox.logger)

        DefaultTeardownLogic.power_off_and_delete_all_vm_resources(api = api,
                                                                   reservation_details =reservation_details,
                                                                   reservation_id=sandbox.id,
                                                                   logger=sandbox.logger, components=sandbox.components)

        DefaultTeardownLogic.cleanup_connectivity(api=api,
                                                  reservation_id=sandbox.id,
                                                  logger=sandbox.logger)

