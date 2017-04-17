# coding=utf-8
from abc import ABCMeta
from abc import abstractmethod

class RepositoryClient(object):
    __metaclass__ = ABCMeta

    def __init__(self, sandbox, repository_resource):
        self.sandbox = sandbox
        self.repository_resource = repository_resource

    @abstractmethod
    def download(self, source, destination):
       raise NotImplementedError('subclasses must override download()!')

