from cloudshell.sandbox.orchestration.sandbox_manager import SandboxManager



def conf_func1(sandbox):
    """
    :param SandboxManager sandbox:
    :return:
    """
    sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                message="conf_func1 :-)")


def conf_func2(sandbox):
    """
    :param SandboxManager sandbox:
    :return:
    """
    sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                                message="conf_func2 :-)")


sandbox = SandboxManager()

sandbox.api.WriteMessageToReservationOutput(reservationId=sandbox.reservation_id,
                                            message="Something started :-)")

sandbox.on_configuration_ended(conf_func1, None, None)
sandbox.on_configuration_ended(conf_func2, None, None)

sandbox.execute()

sandbox.api.WriteMessageToReservationOutput(reservationId= sandbox.reservation_id,
                                            message="Something ended :-)")
