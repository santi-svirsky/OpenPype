""" Addon class definition and Settings definition must be imported here.

If addon class or settings definition won't be here their definition won't
be found by OpenPype discovery.
"""

# from .module import HsToolsModule

# __all__ = ("HsToolsModule",)


from .addon import (
    HsToolsAddonSettingsDef,
    HsToolsAddon
)

__all__ = (
    "HsToolsAddonSettingsDef",
    "HsToolsAddon"
)
