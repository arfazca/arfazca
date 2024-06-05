#!/bin/bash

# Function to remove duplicates from a file
remove_duplicates() {
    local file="$1"
    if [[ -f "$file" ]]; then
        sort "$file" | uniq > "${file}.tmp" && mv "${file}.tmp" "$file"
        echo "Processed $file"
    fi
}

# Export the function so it can be used by find -exec
export -f remove_duplicates

# Find all .txt files recursively and remove duplicates
find . -type f -name "*.txt" -exec bash -c 'remove_duplicates "$0"' {} \;


