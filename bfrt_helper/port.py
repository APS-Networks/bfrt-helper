from enum import Enum


class PortSpeed(Enum):
    SPEED_NONE              = "BF_SPEED_NONE"
    SPEED_1G                = "BF_SPEED_1G"
    SPEED_10G               = "BF_SPEED_10G"
    SPEED_25G               = "BF_SPEED_25G"
    SPEED_40G               = "BF_SPEED_40G"
    SPEED_40G_NB            = "BF_SPEED_40G_NB"
    SPEED_40G_NON_BREAKABLE = "BF_SPEED_40G_NON_BREAKABLE"
    SPEED_50G               = "BF_SPEED_50G"
    SPEED_100G              = "BF_SPEED_100G"
    SPEED_200G              = "BF_SPEED_200G"
    SPEED_400G              = "BF_SPEED_400G"

class PortFEC(Enum):
    NONE         = "BF_FEC_TYP_NONE"
    FIRECODE     = "BF_FEC_TYP_FIRECODE"
    REED_SOLOMON = "BF_FEC_TYP_REED_SOLOMON"
    FC           = "BF_FEC_TYP_FC"
    RS           = "BF_FEC_TYP_RS"

class PortAN(Enum):
    DEFAULT = "PM_AN_DEFAULT"
    ENABLE  = "PM_AN_FORCE_ENABLE"
    DISABLE = "PM_AN_FORCE_DISABLE"