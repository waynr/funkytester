#/usr/bin/env bash

# Prepare the local directory after git clone.

# Prepare SETUID binaries 
FILES="./bin/jamplayer "
sudo chown root.root ${FILES}
sudo chmod 777 ${FILES}
sudo chmod ug+s ${FILES}
