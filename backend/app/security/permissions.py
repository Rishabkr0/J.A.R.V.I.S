from enum import Enum

class PermissionLevel(str, Enum):
    SAFE = 'SAFE'
    CONFIRMATION_REQUIRED = 'CONFIRMATION_REQUIRED'
    HIGH_RISK = 'HIGH_RISK'
    BLOCKED = 'BLOCKED'
