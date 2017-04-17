# coding=utf-8
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
from time import gmtime, strftime
import traceback


# ===================================
# ===================================
class ConfigFileManager:
    def __init__(self, sandbox):
        """
        :param SandboxBase sandbox:  The sandbox the config file mgr will work with
        """
        self.sandbox = sandbox

    # ----------------------------------
    # ----------------------------------
    def create_concrete_config_from_template(self, template_config_data, config_set_pool_data,
                                             resource):
        """
        Replace parameters in the template file with concrete values
        Parameters in the template file are marked with {}
        :param str template_config_data:  The data from the config template file
        :param dict config_set_pool_data:  A dictionary with the data from the config set pool
        :param ResourceBase resource:  The resource we want to create the config file for
        """
        try:
            concrete_config_data = template_config_data
            # Replace {ConfigPool.PARAM} with PARAM's value from the pool
            it = re.finditer(r"\{ConfigPool\:[^}]*\}", concrete_config_data, flags=re.IGNORECASE)
            for match in it:
                param = match.group()
                concrete_config_data = concrete_config_data.replace(param, config_set_pool_data[param.lower()])

            # Replace {QUALI-NOTATION} WITH A NOTE
            it = re.finditer(r"\{QUALI NOTATION\}", concrete_config_data,flags=re.IGNORECASE)
            for match in it:
                param = match.group()
                quali_note = "Built from template: " + strftime("%Y-%b-%d %H:%M:%S", gmtime())
                concrete_config_data = concrete_config_data.replace(param, quali_note)

            # Replace {Device.Self.Name} with the resource's name
            it = re.finditer(r"\{Device:Self:Name\}", concrete_config_data,flags=re.IGNORECASE)
            for match in it:
                param = match.group()
                concrete_config_data = concrete_config_data.replace(param, resource.name)

            # Replace {Device.Self.Address} with the resource's management ip
            it = re.finditer(r"\{Device:Self:Address\}", concrete_config_data,flags=re.IGNORECASE)
            for match in it:
                param = match.group()
                concrete_config_data = concrete_config_data.replace(param, resource.address)

            # Replace {Device.Self.ATTRIBUTE_NAME} with the resource's attribute value
            # Need to decode password attributes: Password, Enable Password, and SNMP Read Community
            it = re.finditer(r"\{Device:Self\:[^}]*\}", concrete_config_data,flags=re.IGNORECASE)
            for match in it:
                param = match.group()
                idx = param.rfind(':')+1
                att_name = param[idx:len(param)-1]
                param_val = resource.get_attribute(att_name)
                #param_val = resource.get_attribute(param)
                concrete_config_data = concrete_config_data.replace(param, param_val)

            # Replacemant of params from types: {Device:ALIAS:Attribute_name}
            root_resources = self.sandbox.get_root_resources()
            it = re.finditer(r"\{Device:[^}]*\}", concrete_config_data, flags=re.IGNORECASE)
            for match in it:
                param = match.group()
                junk, sb_alias, alias_attribname = param.split(":")
                alias_attribname = alias_attribname.replace("}","")
                concrete_name = ''
                for resource in root_resources:
                    if resource.alias == sb_alias:
                        concrete_name = resource.name
                        param_val = resource.get_attribute(alias_attribname)
                        concrete_config_data = concrete_config_data.replace(param, param_val)
                        break
                if concrete_name <= ' ':
                    raise ("did not find concrete device with alias name " + sb_alias)

            return concrete_config_data
        except:
            print str(Exception.message)
            self.sandbox.report_error("Failed to create a concrete config file from the template\'s data. "
                                      "Unexpected error: " + traceback.format_exc())
