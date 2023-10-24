"""
This module contains constants.
"""
import os


__table_prefix = f"{os.environ['PROJECT_NAME']}-{os.environ['GEODE_ENVIRONMENT']}"

ALLOWED_REMOTE_CONFIGS_CONDITIONS = ("available_applications", "available_countries")

TABLE_ABTESTS = f"{__table_prefix}-abtests"
TABLE_ABTESTS_HISTORY = f"{__table_prefix}-abtests-history"
TABLE_REMOTE_CONFIGS = f"{__table_prefix}-remote-configs"
TABLE_REMOTE_CONFIGS_CONDITIONS = f"{__table_prefix}-remote-configs-conditions"
TABLE_USERS_ABTESTS = f"{__table_prefix}-users-abtests"
