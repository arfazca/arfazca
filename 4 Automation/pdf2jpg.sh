#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: No PDF file specified."
  exit 1
fi

gs -dNOPAUSE -sDEVICE=jpeg -r200 -dJPEGQ=100 -sOutputFile=outJPG.jpg "$1" -dBATCH
