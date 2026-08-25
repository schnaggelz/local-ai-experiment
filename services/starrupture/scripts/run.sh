#!/usr/bin/env bash
set -e

APP_ID=3809400

echo "Installing ..."
/home/steam/steamcmd/steamcmd.sh \
    +force_install_dir /home/steam/starrupture \
    +login anonymous \
    +app_update 3809400 validate \
    +quit

echo "Launching ..."
cd /home/steam/starrupture
