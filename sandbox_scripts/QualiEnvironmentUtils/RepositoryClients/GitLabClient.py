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
        self.repository_path = repository_resource.get_attribute("Repository Path")

    def download(self, source, destination):
        #print "GitLabClient called!"
        #print "   " + source
        #print "   " + destination
        gl = gitlab.Gitlab(self.url, self.token)
        projid = 0
        projects = ''
        try:
            for project in gl.getall(gl.getprojects):
                #print project['name']
                if project['name'] == self.project_name:
                    projid = project['id']
                    break
                else:
                    projects += str(project['id']) + '-' + project['name'] + '\n'
        except:
            return 4, "ERROR: Could not access repository at %s" % self.url

        if projid == 0:
            return 3, "ERROR: Failed to locate project by name among \n" + projects

        try:
            source = self.repository_path + source
            filebase64 = gl.getfile(projid, source, 'master')
            filetext = base64.b64decode(filebase64['content']).decode()
        except:
            return 2, "ERROR: Failed to retrieve file."

        try:
            with open(destination,'w') as dest:
                    dest.write(filetext)
            print "Downloaded: " + source
            return 0, "Successfully retrieved file from repository and saved to destination"
        except:
            return 1, "ERROR: Retrieved file from repository - failed to save to destination"
