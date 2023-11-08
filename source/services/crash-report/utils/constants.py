"""
This module contains constants.
"""
import os


ANALYTICS_BUCKET = os.environ["ANALYTICS_BUCKET"]
ANALYTICS_DATABASE = os.environ["ANALYTICS_DATABASE"]
ANALYTICS_TABLE = os.environ["ANALYTICS_TABLE"]

APPLICATIONS_TABLE = os.environ["APPLICATIONS_TABLE"]
CRASHES_TABLE = os.environ["CRASHES_TABLE"]

RATE_CRASH_FREE_SESSIONS_THRESHORD = 95

REGION_NAME = os.environ["AWS_REGION"]

UNITY_CRASH_URL = "https://dashboard.unity3d.com/gaming/organizations/1374503911903/projects/%%PROJECT_ID%%/cloud-diagnostics/crashes-exceptions?tag=%21%3DClosed"
UNITY_PROJECTS = {
    "coeurdegem_android": "bf023568-3ec6-4da9-a1f4-7895c17ec10e",
    "coeurdegem_ios": "bf023568-3ec6-4da9-a1f4-7895c17ec10e",
    "dazzly_android": "60247dd2-4b7d-4844-bd57-9d235790d6da",
    "dazzly_ios": "60247dd2-4b7d-4844-bd57-9d235790d6da",
    "dazzlymatch_android": "8085f94e-9fae-4dd9-b99e-ddc6739db461",
    "dazzlymatch_ios": "8085f94e-9fae-4dd9-b99e-ddc6739db461",
    "dazzlystories_android": "06d7bbb4-f872-448b-afb8-33805c9ccfcc",
    "dazzlystories_ios": "06d7bbb4-f872-448b-afb8-33805c9ccfcc",
}
