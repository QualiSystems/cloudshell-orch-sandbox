import re
import sys

import nose
from nose.plugins import DefaultPluginManager

c = nose.config.Config()
c.plugins=DefaultPluginManager()
c.srcDirs = ['cloudshell-orch-core']

#c.ignoreFiles.append(re.compile(r'^setup\.py$'))

if not nose.run(config=c):
    sys.exit(1)