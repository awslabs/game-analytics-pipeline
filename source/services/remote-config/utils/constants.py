"""
This module contains constants.
"""
import os


__table_prefix = f"analytics-{os.environ['GEODE_ENVIRONMENT']}"

MAX_ACTIVATED_ABTESTS = 4

TABLE_ABTESTS = f"{__table_prefix}-abtests"
TABLE_ABTESTS_HISTORY = f"{__table_prefix}-abtests-history"
TABLE_REMOTE_CONFIGS = f"{__table_prefix}-remote-configs"
TABLE_USERS_ABTESTS = f"{__table_prefix}-users-abtests"