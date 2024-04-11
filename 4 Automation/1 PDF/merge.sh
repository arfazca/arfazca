#!/bin/bash

# Check if at least two files are provided
if [ $# -lt 2 ]; then
    echo "Please provide at least two PDF files to merge."
    exit 1
fi

# Check if all provided files exist
for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "File $file not found!"
        exit 1
    fi
done

# Define the output file
out="merged.pdf"

# Run the gs command
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile="$out" "$@"

# Check if the gs command was successful
if [ $? -eq 0 ]; then
    echo "PDF files merged successfully."
else
    echo "An error occurred while merging the PDF files."
    exit 1
fi