remote_config_dist_dir="$PWD/remote-config-assets"
source_dir="$PWD/../source"

echo "------------------------------------------------------------------------------"
echo "Copying Remote Config project"
echo "------------------------------------------------------------------------------"
echo "rm -rf $remote_config_dist_dir"
rm -rf $remote_config_dist_dir
echo "mkdir -p $remote_config_dist_dir"
mkdir -p $remote_config_dist_dir

rsync -av --exclude='.venv/' $source_dir/services/remote-config/* $remote_config_dist_dir >/dev/null
sed -i '' s/%%ENVIRONMENT%%/$1/g $remote_config_dist_dir/zappa_settings.json
sed -i '' s/%%AWS_REGION%%/$2/g $remote_config_dist_dir/zappa_settings.json

echo "------------------------------------------------------------------------------"
echo "Build Remote Config project"
echo "------------------------------------------------------------------------------"

cd $remote_config_dist_dir
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt >/dev/null
zappa deploy
if [[ $? == 1 ]]; then
    echo "Applicaton already created, will update it"
    zappa update
fi
cd -
