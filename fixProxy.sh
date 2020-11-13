#!/bin/bash

# This script configures settings that configure an infrastructure VM
# to work with a) the proxy servers in the matrix lab and
# b) the artifactory instance we use to mirror the Cannonical upstream
# for Ubuntu packages.

set +e
set -o pipefail

ARTIFACTORY_URL=https://artifactory.rspringob.local/artifactory
ARTIFACTORY_KEY_REPO="${ARTIFACTORY_URL}/keys.gnupg.net-local"

#-----------------------------------------------------
# Fix pip.
#-----------------------------------------------------
pip_use_artifactory() {
    PIP_FILE=/etc/pip.conf

    # Configure pip to use artifactory
    echo "[global]" >> $PIP_FILE
    echo "trusted-host = artifactory.rspringob.local" >> $PIP_FILE
    echo "index-url = https://artifactory.rspringob.local/artifactory/api/pypi/pypi-virtual/simple" >> $PIP_FILE
}

#-----------------------------------------------------
# Add the simplivt root certificate
#-----------------------------------------------------
add_simplivt_root_ca() {
    SIMPLIVT_CERT=ca.rspringob.local.crt
    CERT_STORE=/usr/local/share/ca-certificates
    wget -q --no-check-certificate -O "${CERT_STORE}/${SIMPLIVT_CERT}" "${ARTIFACTORY_KEY_REPO}/${SIMPLIVT_CERT}"
    update-ca-certificates
}

#-----------------------------------------------------
# Add the artifactory apt key to apt
#-----------------------------------------------------
add_apt_key() {
    APT_REPO_KEY=ras-repo.key
    wget -q --no-check-certificate -O - "${ARTIFACTORY_KEY_REPO}/${APT_REPO_KEY}" | apt-key add -
}

#-----------------------------------------------------
# Adjust apt sources  - expects one arg - the distro name (e.g. 'buster')
# We want things to look like
# deb http://deb.debian.org/debian stretch main
# deb http://deb.debian.org/debian stretch-updates main
# deb http://security.debian.org/debian-security stretch/updates main
#-----------------------------------------------------
update_apt_source_list() {
    APT_SOURCES_FILE=/etc/apt/sources.list
    # Configure the sources list to point to artifactory.
    # Move the old sources file.
    mv $APT_SOURCES_FILE "${APT_SOURCES_FILE}.old"

    echo "deb https://artifactory.rspringob.local/artifactory/debian-mirror ${1} main" >> $APT_SOURCES_FILE
    echo "deb https://artifactory.rspringob.local/artifactory/debian-mirror ${1}-updates main" >> $APT_SOURCES_FILE
    echo "deb https://artifactory.rspringob.local/artifactory/debian-security-mirror ${1}/updates main" >> $APT_SOURCES_FILE
}

add_simplivt_root_ca
pip_use_artifactory
add_apt_key
update_apt_source_list buster
