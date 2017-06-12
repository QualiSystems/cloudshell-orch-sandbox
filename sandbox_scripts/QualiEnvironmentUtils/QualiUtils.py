# coding=utf-8


class QualiError(Exception):
    def __init__(self, name, message):
        self.message = message
        self.name = name

    def __str__(self):
        return 'CloudShell error at ' + self.name + '. Error is: ' + self.message

class rsc_run_result_struct:
    def __init__(self, resource_name):
        self.run_result = True
        self.resource_name = resource_name
        self.message = ""
