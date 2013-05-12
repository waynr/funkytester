# this is fairly standard set-up that nees to be done before running dialog but
# which can be a little overwhelming to look at for people who aren't used to
# working with this code. 

# WARNING: this file assumes that the sourcing file has already sourced
# lib/emac_test_functions.lib.sh

export LANG=en_US.UTF-8
DIALOG=$(which dialog)

tempfile=$(tempfile 2>/dev/null) || tempfile=/tmp/test$$
trap "rm -rf $tempfile" 0 1 2 5 15

if [ "$(which dialog)" == "" ] || [ "$(which resize)" == "" ] ;then
    echo "This script requires the resize and dialog packages. Please install and try again."
    rm -f $tempfile
    exit 1
fi

util_source_resize

