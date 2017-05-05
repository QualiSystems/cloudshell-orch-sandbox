from RepositoryClient import *
from sandbox_scripts.QualiEnvironmentUtils.Sandbox import *
import base64
import pip

try:
    imported_gitlab = True
    import gitlab
except:
    try:
        pip.main(["install","pyapi-gitlab"])
        import gitlab
    except:
        imported_gitlab = False


class GitLabClient(RepositoryClient):
    # ----------------------------------
    # ----------------------------------
    def __init__(self, sandbox,repository_resource ):
        super(GitLabClient,self).__init__(sandbox, repository_resource)
        if imported_gitlab == False:
            self.sandbox.report_error('gitlab lib was not found', write_to_output_window=True)
        self.url = repository_resource.get_attribute("GitLab URL")
        self.token = repository_resource.get_attribute("GitLab Token")
        self.project_name = repository_resource.get_attribute("GitLab Project Name")
        self.repository_path = repository_resource.get_attribute("Repository Path")

    # ----------------------------------
    # ----------------------------------
    def download(self, source, destination):

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
        except Exception as ex:
            raise QualiError("GitLabClient", "ERROR: Could not access repository at %s" % self.url + " : " + str(ex.message))

        if projid == 0:
            raise QualiError("GitLabClient","ERROR: Failed to locate project by name among \n" + projects)

        try:
            source = self.repository_path + source
            filebase64 = gl.getfile(projid, source, 'master')
            filetext = base64.b64decode(filebase64['content']).decode()
        except Exception as ex:
            raise QualiError("GitLabClient", "ERROR: Failed to retrieve file, which may be expected for " +
                             source + " : " + str(ex.message))

        try:
            with open(destination,'w') as dest:
                    dest.write(filetext)
            return 0, "Successfully retrieved file from repository and saved to destination"
        except Exception as ex:
            raise QualiError("GitLabClient","ERROR: Retrieved file from repository - failed to save to destination : " + str(ex.message))
