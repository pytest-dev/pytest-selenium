#!/usr/bin/env bash

set -e

version=${1:-latest}

install_dir="/usr/local/bin"
base_url="https://github.com/mozilla/geckodriver/releases/download"

if [[ ${version} == "latest" ]]; then
    json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
    version=$(echo "${json}" | jq -r '.tag_name')
else
    version="v${version}"
fi


[[ $(uname) == "Darwin" ]] && os="macos" || os="linux64"

curl -sL "${base_url}/${version}/geckodriver-${version}-${os}.tar.gz" | tar -xz
mv geckodriver "${install_dir}"
echo "geckodriver ${version} is now available in '${install_dir}'"
