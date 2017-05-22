import unittest
from unittest import TestCase

from cloudshell.api.cloudshell_api import GetReservationDescriptionResponseInfo, ReservationDescriptionInfo
from mock import create_autospec, patch, Mock

from cloudshell.workflow.orchestration.sandbox import Sandbox
from workflow.orchestration.components import Components


class test_helpers(object):
    @staticmethod
    def create_reservation_details():
        xml = '''<?xml version="1.0" encoding="utf-16"?>
                    <Response CommandName="GetReservationDetails" Success="true" xmlns="http://schemas.qualisystems.com/ResourceManagement/ApiCommandResult.xsd" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                      <ErrorCode>0</ErrorCode>
                      <ResponseInfo xsi:type="GetReservationDescriptionResponseInfo">
                        <ReservationDescription Id="0ba4f671-50f4-420a-ba34-07bfd4b73c87" Name="Configuration Managment" Description="Blueprint with preconfigured setup &amp; teardown processes.Deploys Apps and resolves connections on Setup, and deletes App VMs on Teardown" StartTime="22/05/2017 10:26:00" EndTime="22/05/2017 12:36:00" RecurrenceType="None" Owner="admin" Booked="true" Status="Started" ProvisioningStatus="Ready" ActualEndTime="" CreateDate="22/05/2017 10:26:51" ModificationDate="22/05/2017 10:29:33" DomainName="Global">
                          <Topologies>
                            <TopologyName>Configuration Managment</TopologyName>
                          </Topologies>
                          <TopologiesInfo>
                            <Topology Name="Configuration Managment" Alias="Configuration Managment">
                              <Type>Regular</Type>
                              <State>Pending</State>
                            </Topology>
                          </TopologiesInfo>
                          <PermittedUsers>
                            <PermittedUser>admin</PermittedUser>
                          </PermittedUsers>
                          <Resources>
                            <ReservedResource Name="Database_47a603aa" FolderFullPath="Deployed Apps" FullAddress="192.168.65.73" Shared="false" Availability="Available" Locked="false" Released="false" ResourceFamilyName="Generic App Family" ResourceModelName="Generic App Model" CreatedByUser="admin" CreatedInDomain="Global" CreatedInReservation="0ba4f671-50f4-420a-ba34-07bfd4b73c87">
                              <VmDetails UID="42327185-1640-4292-7dac-ff9c06de4a18" CloudProviderFullName="testing">
                                <VmCustomParams>
                                  <VmCustomParam Name="auto_delete" Value="True" />
                                  <VmCustomParam Name="refresh_ip_timeout" Value="600" />
                                  <VmCustomParam Name="wait_for_ip" Value="True" />
                                  <VmCustomParam Name="auto_power_off" Value="True" />
                                  <VmCustomParam Name="ip_regex" Value="" />
                                  <VmCustomParam Name="autoload" Value="True" />
                                  <VmCustomParam Name="auto_power_on" Value="True" />
                                </VmCustomParams>
                              </VmDetails>
                              <AppDetails AppName="Database" />
                            </ReservedResource>
                            <ReservedResource Name="Application-server" FolderFullPath="" FullAddress="1.2.3.4" Shared="true" Availability="Available" Locked="false" Released="false" ResourceFamilyName="Deployed App" ResourceModelName="Generic Deployed App" CreatedByUser="admin" CreatedInDomain="Global" />
                            <ReservedResource Name="Web Server_46906455" FolderFullPath="Deployed Apps" FullAddress="192.168.65.75" Shared="false" Availability="Available" Locked="false" Released="false" ResourceFamilyName="Generic App Family" ResourceModelName="Generic App Model" CreatedByUser="admin" CreatedInDomain="Global" CreatedInReservation="0ba4f671-50f4-420a-ba34-07bfd4b73c87">
                              <VmDetails UID="4232986e-7675-ed1b-e1de-eb70e02705cb" CloudProviderFullName="testing">
                                <VmCustomParams>
                                  <VmCustomParam Name="wait_for_ip" Value="True" />
                                  <VmCustomParam Name="auto_power_on" Value="True" />
                                  <VmCustomParam Name="autoload" Value="True" />
                                  <VmCustomParam Name="ip_regex" Value="" />
                                  <VmCustomParam Name="auto_delete" Value="True" />
                                  <VmCustomParam Name="auto_power_off" Value="True" />
                                  <VmCustomParam Name="refresh_ip_timeout" Value="600" />
                                </VmCustomParams>
                              </VmDetails>
                              <AppDetails AppName="Web Server" />
                            </ReservedResource>
                          </Resources>
                          <TopologiesReservedResources>
                            <TopologyReservedResource Name="Application-server" FolderFullPath="" FullAddress="1.2.3.4" Shared="true" Availability="Available" Locked="false" Released="false" ResourceFamilyName="Deployed App" ResourceModelName="Generic Deployed App" CreatedByUser="admin" CreatedInDomain="Global" TopologyName="Configuration Managment" Alias="Application-server" />
                          </TopologiesReservedResources>
                          <Conflicts />
                          <TopologiesRouteInfo>
                            <TopologyRoutes TopologyName="Configuration Managment">
                              <Routes />
                            </TopologyRoutes>
                          </TopologiesRouteInfo>
                          <TopologiesResourcesAttributeInfo />
                          <TopologiesInstructionsInfo>
                            <TopologyInstructions TopologyName="Configuration Managment">
                              <Instructions />
                            </TopologyInstructions>
                          </TopologiesInstructionsInfo>
                          <ActiveRoutesInfo />
                          <RequestedRoutesInfo />
                          <Connectors />
                          <Apps />
                          <ReservationLiveStatus ReservationId="0ba4f671-50f4-420a-ba34-07bfd4b73c87" />
                          <SetupStage>Ended</SetupStage>
                          <Services />
                        </ReservationDescription>
                      </ResponseInfo>
                    </Response>'''
        return GetReservationDescriptionResponseInfo(xml, None)

    @staticmethod
    def some_function(sandbox, components):
        pass


class TestSandbox(TestCase):
    def setUp(self):
        self.helpers_patcher = patch('cloudshell.workflow.orchestration.sandbox.helpers')
        self.qs_logger_patcher = patch('cloudshell.workflow.orchestration.sandbox.get_qs_logger')

        helpers = self.helpers_patcher.start()
        logger = self.qs_logger_patcher.start()

        get_api_session = Mock()
        reservation_description = Mock(spec=ReservationDescriptionInfo)
        reservation_description.Resources = []
        reservation_description.Services = []
        reservation_description.Apps = []

        reservation_details = Mock(spec=GetReservationDescriptionResponseInfo)
        reservation_details.ReservationDescription = reservation_description

        helpers.get_api_session.return_value = get_api_session
        get_api_session.GetReservationDetails.return_value = reservation_details


        # helpers.get_api_session.GetReservationDetails.return_value = GetReservationDetails
        self.sandbox = Sandbox()

    def test_sandbox_workflow_provisioning_event_registration(self):
        resources = self.sandbox.components.get_resources_by_model('model_name')
        self.sandbox.workflow.add_to_provisioning(test_helpers.some_function,resources)
        self.assertEqual(len(self.sandbox.workflow._provisioning_functions), 1)

    def tearDown(self):
        self.helpers_patcher.stop()
        self.qs_logger_patcher.stop()


if __name__ == '__main__':
    unittest.main()
