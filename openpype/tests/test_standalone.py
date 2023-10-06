print("hello world")
# import openpype

import openpype.hosts.nuke

from openpype.pipeline import install_host
from openpype.hosts.nuke.api import NukeHost


host = NukeHost()
# install_host(host)

print(dir(host))
print("Success!")