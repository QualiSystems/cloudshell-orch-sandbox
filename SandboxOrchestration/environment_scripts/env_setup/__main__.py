from cloudshell.sandbox.orchestration.sandbox_manager import SandboxManager



def conf_func(sandbox):
    """
    :param SandboxManager sandbox:
    :return:
    """
    sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                message="conf_func :-)")


sandbox = SandboxManager()

sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                            message="Something started :-)")

sandbox.on_configuration_ended(conf_func, None, None)

sandbox.execute()

sandbox.api.WriteMessageToReservationOutput(reservationId= sandbox.reservation_id,
                                            message="Something ended :-)")
