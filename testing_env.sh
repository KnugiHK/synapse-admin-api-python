#!/bin/bash

sudo apt install build-essential python3-dev libffi-dev \
                 sqlite3 libssl-dev libjpeg-dev libxslt1-dev \
                 python3-venv libyaml-dev -y

if [ ! -d synapse_test ]; then
	mkdir -p synapse_test
	python3 -m venv synapse_test/env
	source synapse_test/env/bin/activate
	pip install --upgrade flake8 pytest matrix-synapse .
fi
cd synapse_test
python -m synapse.app.homeserver \
    --server-name localhost \
    --config-path homeserver.yaml \
    --generate-config \
    --report-stats=no


latest_yq=$(wget -qO- https://github.com/mikefarah/yq/releases/latest | egrep -o 'v[0-9]\.[0-9]{2}\.[0-9]' | uniq)
sudo wget -qO /usr/bin/yq "https://github.com/mikefarah/yq/releases/download/$latest_yq/yq_linux_amd64" && sudo chmod +x /usr/bin/yq

# Enable server notices
cat << EOF >> homeserver.yaml

server_notices:
  system_mxid_localpart: notices
  system_mxid_display_name: "Server Notices"
  system_mxid_avatar_url: "mxc://server.com/oumMVlgDnLYFaPVkExemNVVZ"
  room_name: "Server Notices"
rc_login:
  address:
    per_second: 0.1
    burst_count: 20
  account:
    per_second: 0.1
    burst_count: 20
  failed_attempts:
    per_second: 0.1
    burst_count: 20
EOF


synctl start

register_new_matrix_user -c homeserver.yaml -a -u admin1 -p 0123456789 http://localhost:8008
register_new_matrix_user -c homeserver.yaml --no-admin -u test1 -p 123456789 http://localhost:8008
netstat -ltp
wget -O - http://localhost:8008/_matrix/client/versions

login1=$(curl -s 'http://localhost:8008/_matrix/client/r0/login' --compressed \
-H 'Content-Type: application/json' --data-raw '{"type":"m.login.password",
"password":"123456789","identifier":{"type":"m.id.user","user":"test1"},
"initial_device_display_name":"Testing curl"}')
echo "$login1" | grep -oP '(?<="access_token":").*?(?=")' > user.token

login2=$(curl -s 'http://localhost:8008/_matrix/client/r0/login' --compressed \
-H 'Content-Type: application/json' --data-raw '{"type":"m.login.password",
"password":"0123456789","identifier":{"type":"m.id.user","user":"admin1"},
"initial_device_display_name":"Testing curl"}')
echo "$login2" | grep -oP '(?<="access_token":").*?(?=")' > admin.token
if [ ! -s admin.token ] | [ ! -s user.token ]; then
    echo "Error in retrieving access tokens. Could there be a Synapse instance running?"
    synctl stop
    exit 2
fi

cd ..
pytest -v
cd synapse_test
synctl stop
# rm -rf synapse_test
