analytics_backoffice_dist_dir="$PWD/analytics-backoffice-assets"
source_dir="$PWD/../source"

echo "------------------------------------------------------------------------------"
echo "Copying Analytics Backoffice project"
echo "------------------------------------------------------------------------------"
echo "rm -rf $analytics_backoffice_dist_dir"
rm -rf $analytics_backoffice_dist_dir
echo "mkdir -p $analytics_backoffice_dist_dir"
mkdir -p $analytics_backoffice_dist_dir

rsync -av --exclude='.venv/' $source_dir/services/analytics-backoffice/* $analytics_backoffice_dist_dir >/dev/null
sed -i '' s/%%AWS_REGION%%/$2/g $analytics_backoffice_dist_dir/zappa_settings.json
sed -i '' s/%%PROJECT_NAME%%/$3/g $analytics_backoffice_dist_dir/zappa_settings.json
sed -i '' s/%%GEODE_DOMAIN_NAME%%/$4/g $analytics_backoffice_dist_dir/zappa_settings.json
sed -i '' s/%%PROFILE_NAME%%/$AWS_PROFILE/g $analytics_backoffice_dist_dir/zappa_settings.json

echo "------------------------------------------------------------------------------"
echo "Build Analytics Backoffice project"
echo "------------------------------------------------------------------------------"

cd $analytics_backoffice_dist_dir
rm -r .venv 2>/dev/null
python3 -m venv .venv --upgrade-deps
source .venv/bin/activate
pip install -r requirements.txt >/dev/null
zappa update $1
if [[ $? == 1 ]]; then
    echo "Applicaton not exists, will create it"
    zappa deploy $1
fi
cd -
