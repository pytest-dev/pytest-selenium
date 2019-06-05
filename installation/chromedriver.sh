#!/usr/bin/env bash

set -e

version=${1:-latest}

install_dir="/usr/local/bin"
drivername="chromedriver"
base_url="https://${drivername}.storage.googleapis.com"

[[ ${version} == "latest" ]] && version=$(curl -s "${base_url}/LATEST_RELEASE")

[[ $(uname) == "Darwin" ]] && os="mac" || os="linux"

filename="${drivername}_${os}64.zip"
curl -sL -o /tmp/"${filename}" "${base_url}/${version}/${filename}"
unzip -q /tmp/"${filename}"
mv ${drivername} "${install_dir}"

[[ $(uname) == "Linux" ]] && chmod +x "${install_dir}/${drivername}"

echo "${drivername} ${version} is now available in '${install_dir}'"
