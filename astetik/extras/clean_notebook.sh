#!/bin/bash

# Jupyter HTML Output Cleaner
# removes 'out' and 'toggle code cells' from html files in a given folder.

while read FILE
do

	sed 's/<a href="javascript:code_toggle()">toggle code cells<\/a>//' $FILE > temp.html
	sed 's/D84315/ffffff/' temp.html > $FILE

done < <(ls *.html)
