from sandbox_scripts.environment.setup.setup_script import EnvironmentSetup
from sandbox_scripts.environment.setup.setup_resources import EnvironmentSetupResources
from sandbox_scripts.environment.setup.setup_VM import EnvironmentSetupVM


def main():
    EnvironmentSetup().execute()
    EnvironmentSetupVM().execute()
    EnvironmentSetupResources().execute()

if __name__ == "__main__":
    main()
