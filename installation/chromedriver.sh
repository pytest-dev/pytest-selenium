#!/usr/bin/env bash

set -e

version=${1:-latest}

install_dir="/usr/local/bin"
base_url="https://chromedriver.storage.googleapis.com"

[[ ${version} == "latest" ]] && version=$(curl -s "${base_url}/LATEST_RELEASE")

[[ $(uname) == "Darwin" ]] && os="mac" || os="linux"

filename="chromedriver_${os}64.zip"
curl -sL -o /tmp/"${filename}" "${base_url}/${version}/${filename}"
unzip -q /tmp/"${filename}"
mv chromedriver "${install_dir}"
ls -la "${install_dir}"
chmod +x "${install_dir}"
ls -la "${install_dir}"
echo "chromedriver ${version} is now available in '${install_dir}'"
