from cloudshell.workflow.environment.setup.setup_common import SetupCommon
from cloudshell.workflow.orchestration.sandbox import Sandbox

class DefaultSetupWorkflow(object):
    @staticmethod
    def extend(sandbox, enable_provisioning=True, enable_connectivity=True, enable_configuration=True):
        """
        :param Sandbox sandbox:
        :return:
        """
        sandbox.logger.info("Adding default orchestration")
        if enable_provisioning:
            sandbox.workflow.add_provisioning_process(DefaultSetupWorkflow.default_provisioning, None, None)
        if enable_connectivity:
            sandbox.workflow.add_connectivity_process(DefaultSetupWorkflow.default_connectivity, None, None)
        if enable_configuration:
            sandbox.workflow.add_configuration_process(DefaultSetupWorkflow.default_configuration, None, None)

    @staticmethod
    def default_provisioning(sandbox, resources, steps):
        """
        :param Sandbox sandbox:
        :return:
        """
        api = sandbox.api

        sandbox.logger.info("Executing default provisioning")

        reservation_details = api.GetReservationDetails(sandbox.reservation_id)
        deploy_result = SetupCommon.deploy_apps_in_reservation(api=api,
                                                                    reservation_details=reservation_details,
                                                                    reservation_id=sandbox.reservation_id,
                                                                    logger=sandbox.logger)

        sandbox.components.add_app_deployment_results(deploy_result)

        SetupCommon.validate_all_apps_deployed(deploy_results=deploy_result,
                                               logger=sandbox.logger)

        SetupCommon.try_exeucte_autoload(api=api,
                                         deploy_result=deploy_result,
                                         resource_details_cache=sandbox._resource_details_cache,
                                         reservation_id=sandbox.reservation_id,
                                         logger=sandbox.logger)

    @staticmethod
    def default_connectivity(sandbox, resources, steps):
        """
        :param Sandbox sandbox:
        :return:
        """
        api = sandbox.api

        sandbox.logger.info("Executing default connectivity")

        reservation_details = api.GetReservationDetails(sandbox.reservation_id)

        SetupCommon.connect_all_routes_in_reservation(api=api,
                                                      reservation_details=reservation_details,
                                                      reservation_id=sandbox.reservation_id,
                                                      resource_details_cache=sandbox._resource_details_cache,
                                                      logger=sandbox.logger)

        SetupCommon.run_async_power_on_refresh_ip(api=api,
                                                  reservation_details=reservation_details,
                                                  deploy_results=sandbox.deploy_result,
                                                  resource_details_cache=sandbox._resource_details_cache,
                                                  reservation_id=sandbox.reservation_id,
                                                  logger=sandbox.logger)

    @staticmethod
    def default_configuration(sandbox, resources, steps):
        """
        :param Sandbox sandbox:
        :return:
        """
        sandbox.logger.info("Executing default configuration")
        SetupCommon.configure_apps(api=sandbox.api,
                                   reservation_id=sandbox.reservation_id,
                                   logger=sandbox.logger)
