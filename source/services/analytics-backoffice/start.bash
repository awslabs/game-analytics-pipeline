# This script is used to run analytics-backoffice REST API locally

BRANCH_NAME=`git rev-parse --abbrev-ref HEAD`
export PROJECT_NAME="geode-analytics"

if [ $BRANCH_NAME = "master" ]; then
    export GEODE_ENVIRONMENT="prod"
elif [ $BRANCH_NAME = "dev" ]; then
    export GEODE_ENVIRONMENT="dev"
else
    export GEODE_ENVIRONMENT="sandbox"
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment creation processing...\n"
    python3.11 -m venv .venv --upgrade-deps
    source .venv/bin/activate
    pip install -r requirements.txt > /dev/null
fi

python main.py
