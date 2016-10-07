from sandbox_scripts.environment.teardown.teardown_script import EnvironmentTeardown
from sandbox_scripts.environment.teardown.teardown_resources import EnvironmentTeardownResources
from sandbox_scripts.environment.teardown.teardown_VM import EnvironmentTeardownVM

def main():
    EnvironmentTeardown().execute()
    EnvironmentTeardownVM().execute()
    EnvironmentTeardownResources().execute()

if __name__ == "__main__":
    main()
