"""
This module contains constants.
"""
import os


__table_prefix = f"{os.environ['PROJECT_NAME']}-{os.environ['GEODE_ENVIRONMENT']}"

ANALYTICS_BUCKET = f"{__table_prefix}-analyticsbucket"
ANALYTICS_DATABASE = __table_prefix
ANALYTICS_TABLE = "raw_events"

TABLE_ABTESTS = f"{__table_prefix}-abtests"
TABLE_AUDIENCES = f"{__table_prefix}-audiences"
TABLE_APPLICATIONS = f"{__table_prefix}-applications"
TABLE_REMOTE_CONFIGS = f"{__table_prefix}-remote-configs"
TABLE_REMOTE_CONFIGS_OVERRIDES = f"{__table_prefix}-remote-configs-overrides"
TABLE_REMOTE_CONFIGS_OVERRIDES_HISTORY = f"{__table_prefix}-remote-configs-overrides-history"
TABLE_USERS_ABTESTS = f"{__table_prefix}-users-abtests"
