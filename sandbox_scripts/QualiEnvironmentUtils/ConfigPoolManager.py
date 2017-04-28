# coding=utf-8
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import SandboxBase
from sandbox_scripts.QualiEnvironmentUtils.Resource import ResourceBase
from sandbox_scripts.QualiEnvironmentUtils.QualiUtils import QualiError
import re


class ConfigPoolManager(object):
    def __init__(self, sandbox, pool_resource):
        """
        Check if there is an ip pool
        :param SandboxBase sandbox:  The sandbox the config file mgr will work with
        :param ResourceBase pool_resource:  The pool resource in the sandbox
        """
        self.sandbox = sandbox
        if pool_resource:
            self.pool_resource = pool_resource
        else:
            raise QualiError('ConfigPoolManager', 'Trying to use the ConfigPoolManager without a pool resource')
        self.pool_data = self._pool_data_to_dict()

    # -----------------------------------------
    # Create a dictionary that will hold the data from the pool
    # -----------------------------------------
    def _pool_data_to_dict(self):
        pool_data_dict = dict()
        for attribute in self.pool_resource.attributes:
            pool_data_dict[str('{ConfigPool:' + attribute.Name + '}').lower()] = attribute.Value
        for resource_from_pool in self.pool_resource.details.ChildResources:
            split_name = resource_from_pool.Name.split('/')
            name_of_resource_from_pool = split_name[len(split_name)-1]
            for attribute in resource_from_pool.ResourceAttributes:
                resource_dict_key = str('{ConfigPool:' + name_of_resource_from_pool + ':' +
                                        attribute.Name + '}').lower()
                pool_data_dict[resource_dict_key] = attribute.Value
        return pool_data_dict
