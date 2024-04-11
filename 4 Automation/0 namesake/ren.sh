#!/bin/bash
#!/bin/sh

max=85
hash=" _"
tmStp="$"
fall="a37d7o"
spring="a94d6u"
summer="t50e9u"
sd="#"

directory="/Users/arfaz/Library/CloudStorage/OneDrive-UniversityofVictoria/0 UVIC/3 Co-Op/1 Y3/3B/1 Applications/3 Apr'10x"

baseDir=${directory##*/}
baseDir=${baseDir#*[!0-9]}
month=$(month=$(echo "${baseDir:0:3}" | tr '[:upper:]' '[:lower:]'); echo ${month:0:1}${month: -1})
date=$(echo "${baseDir:3}" | tr -dc '0-9')
namesake="${month}${date}${sd}"

files=()
while IFS= read -r line; do files+=("$line");
done < <(find "$directory" -type f -name "* - Placement Application*" | sed 's/.*\///; s/.*\([Hh]ussain.*\.pdf\)/\1/' | sort -t'$' -k1,1n)
# printf '("%s")\n' "${files[@]}"

for file in "${files[@]}"; do
    if [[ "$file" != *"_"* ]]; then
        # printf "$file\n"
        ((max++))
        nxs=$(sed 's/Placement Application #[0-9]* - /Placement Application - /g' <<< "$file")
        timestamp=$(exiftool -s -s -s -FileCreateDate "$directory/$file" | sed -E 's/.* ([0-9]{2}):([0-9]{2}):([0-9]{2}).*/\1\2\3/')
        nxss="${nxs%% -*} - Placement Application${hash}${spring}${namesake}${tmStp}${timestamp} ${nxs#*Application }"
        mv "$directory/$file" "$directory/$nxss"
    elif [[ "$file" == *"Placement Application -"* && ! "$file" == *"Placement Application #"* ]]; then
        printf "$file\n"
        ((max++))
        timestamp=$(exiftool -s -s -s -FileCreateDate "$directory/$file" | sed -E 's/.* ([0-9]{2}):([0-9]{2}):([0-9]{2}).*/\1\2\3/')
        nxss="${file%% -*} - Placement Application${hash}${spring}${namesake}${max}${tmStp}${timestamp} ${file#*Application }"
        mv "$directory/$file" "$directory/$nxss"
    elif [[ "$file" == *"_"* ]]; then 
        ((max++))
        # exiftool -s -s -s -FileCreateDate "$directory/$file"
        # timestamp=$(exiftool -s -s -s -FileCreateDate "$directory/$file" | sed -E 's/.* ([0-9]{2}):([0-9]{2}):([0-9]{2}).*/\1\2\3/')
        continue;
    fi
done