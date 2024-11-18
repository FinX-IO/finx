# install python
apt install python3 -y
apt update -y
apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget -y
apt update -y
# install pip
apt install python3-pip -y
# install finx-io
pip install -i https://test.pypi.org/simple/ finx-io==1.0.21
# run tests
bash integration_tests.sh
