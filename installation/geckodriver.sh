#!/usr/bin/env bash

set -e

version=${1:-latest}

install_dir="/usr/local/bin"
base_url="https://github.com/mozilla/geckodriver/releases/download"

if [[ ${version} == "latest" ]]; then
    json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
    version=$(echo "${json}" | jq -r '.tag_name')
    [[ ${version} == "null" ]] && version=${GECKO_FALLBACK_VERSION}
else
    version="v${version}"
fi

[[ $(uname) == "Darwin" ]] && os="macos" || os="linux64"

filename="geckodriver-${version}-${os}.tar.gz"
curl -sL -o /tmp/"${filename}" "${base_url}/${version}/${filename}"
echo "try taring to HOME"
tar -zvxf /tmp/"${filename}" -C "${HOME}"
echo "try moving geckodriver to /usr/local/bin"
mv "${HOME}/geckodriver" "${install_dir}"
echo "try taring straight to /usr/bin/local"
tar -zvxf /tmp/"${filename}" -C "${install_dir}"
rm /tmp/"${filename}"
echo "geckodriver ${version} is now available in '${install_dir}'"
