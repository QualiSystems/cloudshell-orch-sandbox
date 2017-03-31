from RepositoryClient import *
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
import base64
try:
    import gitlab
    imported_gitlab = True
except Exception as e:
    imported_gitlab = False

class GitLabClient(RepositoryClient):
    def __init__(self, sandbox,repository_resource ):
        super(GitLabClient,self).__init__(sandbox, repository_resource)
        if imported_gitlab == False:
            self.sandbox.report_error('gitlab lib was not installed', write_to_output_window=True)
        self.url = repository_resource.get_attribute("GitLab URL")
        self.token = repository_resource.get_attribute("GitLab Token")
        self.project_name = repository_resource.get_attribute("GitLab Project Name")

    def download(self, source, destination):
        #TODO - Implement this function
        raise Exception("need to implement")


'''
    def RetrieveFileFromGit (GitURL, GitToken, GitProjectName, TemplateName):
        Git = gitlab.Gitlab(GitURL, GitToken)
        Gitprojid = 0
        Gitprojects = ''
        try:
            for project in Git.getall(Git.getprojects):
                #print project['name']
                if project['name'] == GitProjectName:
                    Gitprojid = project['id']
                    break
                else:
                    Gitprojects += str(project['id']) + '-' + project['name'] + '\n'
        except:
            return 3, "Could not access repository at %s" % GitURL

        if Gitprojid == 0:
            return 2, "Failed to locate project by name among \n" + Gitprojects

        try:
            tmplt64 = Git.getfile(Gitprojid, TemplateName, 'master')
            CfgTemplate = base64.b64decode(tmplt64['content']).decode()
            return 0, CfgTemplate
        except:
            return 1, "Failed to retrieve file."
'''