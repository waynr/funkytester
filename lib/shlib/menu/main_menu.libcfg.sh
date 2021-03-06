# define some geometry settings to be used in a call to dialog that utilize both
# the tailboxbg and the menu commands ( see: templates/template_test.sh )

COL_PADDING=10
RESULTS_WIDTH=$((COLUMNS-(COL_PADDING*2)))

MIN_WIDTH=60

if [ "$COLUMNS" -lt $MIN_WIDTH ] ;then
	MENU_WIDTH=$COLUMNS
else
	MENU_WIDTH=$MIN_WIDTH
fi

ROW_PADDING=2
ROWS_AFTER_PADDING=$((LINES-ROW_PADDING*3))

MENU_ROWS=15
RESULTS_ROWS=$((ROWS_AFTER_PADDING-$MENU_ROWS))

RESULTS_STARTX=$COL_PADDING
MENU_STARTX=$(((RESULTS_WIDTH-MENU_WIDTH)/2+RESULTS_STARTX))

MENU_STARTY=$ROW_PADDING
RESULTS_STARTY=$((MENU_STARTY+MENU_ROWS+ROW_PADDING))

