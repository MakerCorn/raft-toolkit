#!/bin/bash

# Check if a file name is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

# File to split
FILE="$1"

# Desired maximum file size in bytes
MAX_SIZE=199000000  # 10 MB

# Extract filename without path
filename=$(basename "$FILE" .jsonl)

# Using awk to split the file
awk -v max_size="$MAX_SIZE" -v prefix="$filename" '
    BEGIN {
        file_number = 1;
        file_size = 0;
        file_name = sprintf("%s_part_%d.jsonl", prefix, file_number);
    }
    {
        line_size = length($0) + 1; # +1 for newline
        if (file_size + line_size > max_size) {
            close(file_name);
            file_number++;
            file_name = sprintf("%s_part_%d.jsonl", prefix, file_number);
            file_size = 0;
        }
        print $0 > file_name;
        file_size += line_size;
    }
' "$FILE"

echo "Split completed."