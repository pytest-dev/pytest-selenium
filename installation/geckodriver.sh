#!/usr/bin/env bash

set -e

version=${1:-latest}

install_dir="/usr/local/bin"
base_url="https://github.com/mozilla/geckodriver/releases/download"

if [[ ${version} == "latest" ]]; then
    json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
    version=$(echo "${json}" | jq -r '.tag_name')
    # In case of "API rate limit exceeded"
    # See https://developer.github.com/v3/#rate-limiting
    [[ ${version} == "null" ]] && version=${GECKODRIVER_FALLBACK_VERSION}
else
    version="v${version}"
fi

[[ $(uname) == "Darwin" ]] && os="macos" || os="linux64"

filename="geckodriver-${version}-${os}.tar.gz"
curl -sL -o /tmp/"${filename}" "${base_url}/${version}/${filename}"
tar -xf /tmp/"${filename}" -C "${install_dir}"
rm /tmp/"${filename}"
echo "geckodriver ${version} is now available in '${install_dir}'"
