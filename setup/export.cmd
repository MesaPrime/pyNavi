conda activate pyNavi
conda env export > ./setup/environment.yaml
conda list -e ./setup/requirements.txt
pause