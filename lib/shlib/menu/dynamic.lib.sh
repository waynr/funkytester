#!/bin/bash

function create_testmenu() {
    local MENU_DIR="${1-?}"
    local MENU_DIR_prefix=${MENU_DIR%/*}
    local MENU_DIR_suffix=${MENU_DIR#*/}

    local CMD_NAME="${MENU_DIR_suffix}"

    #echo $MENU_DIR_prefix
    #echo $MENU_DIR_suffix
    #local CMD_NAME="${2-?}"

    local menu_message="`cat ${MENU_DIR}/message`"
    local menu_title="`cat ${MENU_DIR}/title`"
    local menu_items="`find ${MENU_DIR} -maxdepth 1 ! -iname *${MENU_DIR_suffix} \
        -type d | sort`"

    local file_name="tmp-testmenu"

    ###### 
    # create script header, initialize function, and invoke dialog:
    cat > ${file_name} <<testmenu_endof_fileheader
#!/bin/bash

. ./config/project.config.sh som_test
. ./lib/emac_test_functions.lib.sh
. ./lib/get_mac.lib.sh
. ./lib/util/output.lib.sh
. ./lib/util/common.lib.sh
. ./lib/menu/common.lib.sh

function ${CMD_NAME}() {
    . ./lib/menu/dialog.libcfg.sh
    . ./lib/menu/main_menu.libcfg.sh

    local STATUS=0

    until [ \$STATUS == 255 ] ;do

	   \$DIALOG --title "${menu_title} Results" \\
		--begin \$RESULTS_STARTY \$RESULTS_STARTX \\
		--tailboxbg \$OUTPUT_FILE \$RESULTS_ROWS \$RESULTS_WIDTH \\
		--and-widget \\
        --title "${menu_title}" \\
	    --cancel-label "Quit" \\
	    --begin \$MENU_STARTY \$MENU_STARTX \\
	    --menu \\
	    "${menu_message}" \$MENU_ROWS \$MENU_WIDTH 8 \\
testmenu_endof_fileheader

    ###### 
    # create dialog menu options
    for entry in ${menu_items} ;do
        local key="`cat ${entry}/key`"
        local description="`cat ${entry}/shortdesc`"

    cat >> ${file_name} <<testmenu_endof_dialogmenu
        "${key}" "${description}" \\
testmenu_endof_dialogmenu

    done

    ###### 
    # finish dialog invocations and set up case statement to handle return
    # value:
    cat >> ${file_name} <<testmenu_casestatements
        2> \$tempfile
	    retval=\$?
	    choice=\$(cat \$tempfile)
        redirect save
	    STATUS=0
        case \$retval in
        0)
            case \$choice in
testmenu_casestatements

    ######
    # Create cases for the case statement
    for entry in ${menu_items} ;do
        local key="`cat ${entry}/key`"
        local action="`cat ${entry}/action`"

    cat >> ${file_name} <<testmenu_dialogactions
            '${key}')
$action
            ;;
testmenu_dialogactions

    done

    ######
    # Finish off the case statements
    cat >> ${file_name} <<testmenu_endof_dialogactions
            *)
            ;;
            esac
            redirect restore
            ;;
        1)
            echo "Cancel pressed."
            rm -rf \$tempfile
            STATUS=1
            redirect restore
            break
            ;;
        255)
            echo "ESQ pressed."
            STATUS=255
            redirect restore
            ;;
        esac
    done

    return 0
}
testmenu_endof_dialogactions

}

function create_menu() {
    local MESSAGE=${1}
    local CMD_NAME=${2}

    local file_name="/tmp/tmp-${RANDOM}"

    ###### 
    # create script header, initialize function, and invoke dialog:
    cat > ${file_name} <<end_of_file_header
#!/bin/bash


function ${CMD_NAME}() {
    . ./lib/util/common.lib.sh

    . ./lib/menu/dialog.libcfg.sh
    . ./lib/menu/main_menu.libcfg.sh

    local STATUS=0

    until [ \$STATUS == 255 ] ;do

        \$DIALOG --title "" \\
	    --cancel-label "Quit" \\
	    --begin \$MENU_STARTY \$MENU_STARTX \\
	    --menu \
	    "${MESSAGE}" \$MENU_ROWS \$MENU_WIDTH 8 \\
end_of_file_header

    ###### 
    # create dialog menu options
    for each in `find /images -maxdepth 1 ! -iname images -type d` ;do
        local dir_name="${each}"
        local description="`cat ${dir_name}/shortdesc`"

    cat >> ${file_name} <<end_of_dialog_menu
        "${each}" "${description}" \\
end_of_dialog_menu

    done

    ###### 
    # finish dialog invocations and set up case statement to handle return
    # value:
    cat >> ${file_name} <<case_statements
        2> \$tempfile
	    retval=\$?
	    choice=\$(cat \$tempfile)
        redirect save
	    STATUS=0
        case \$retval in
        0)
            case \$choice in
case_statements

    ######
    # Create cases for the case statement
    for each in `find /images -maxdepth 1 ! -iname images -type d` ;do
        local dir_name="${each}"

    cat >> ${file_name} <<dialog_actions
            '${each}')
                GLOBAL_TMP_RESULT="${dir_name}"
            ;;
dialog_actions

done

    ######
    # Finish off the case statements
    cat >> ${file_name} <<end_of_dialog_actions
            *)
            ;;
            esac
            redirect restore
            return 0
            ;;
        1)
            echo "Cancel pressed."
            rm -rf \$tempfile
            STATUS=1
            redirect restore
            break
            ;;
        255)
            echo "ESQ pressed."
            STATUS=255
            redirect restore
            ;;
        esac
    done

    return 0
}
end_of_dialog_actions

    ###### 
    # source newly-created function:
    . ${file_name}

    ######
    # add to list of dynamically-generated scripts:
    GLOBAL_GENERATED_SCRIPTS="${file_name} "
    
}
