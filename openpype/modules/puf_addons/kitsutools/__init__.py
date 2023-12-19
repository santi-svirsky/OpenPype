""" Addon class definition and Settings definition must be imported here.

If addon class or settings definition won't be here their definition won't
be found by OpenPype discovery.
"""

# from .module import KitsuToolsModule

# __all__ = ("KitsuToolsModule",)


from .addon import (
    AddonSettingsDef,
    KitsuToolsAddon
)

__all__ = (
    "AddonSettingsDef",
    "KitsuToolsAddon"
)
