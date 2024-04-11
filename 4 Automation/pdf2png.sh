#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: No PDF file specified."
  exit 1
fi

gs -dSAFER -dQUIET -dNOPLATFONTS -dNOPAUSE -dBATCH -sOutputFile="output.png" -sDEVICE=pngalpha -r300 -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -dUseCIEColor -dUseTrimBox -dFirstPage=1 -dLastPage=1 "$1"
