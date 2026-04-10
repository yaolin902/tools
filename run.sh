#!/bin/bash
RED='\033[38;5;203m'
GREEN='\033[38;5;120m'
LIGHT_GRAY='\033[1;30m'
NC='\033[0m' # No Color

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <dir> [dir2 ...] [--delay N] [--filter filter,filter2] [-v|-vv|-vvv]"
  exit 1
fi

verbose=0
delay=0
filter=()
dirs=()
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --delay)
            delay="$2"
            shift 2
            ;;
        --filter)
            IFS=',' read -ra filter <<< "$2"
            shift 2
            ;;
        -v)
            verbose=1
            shift
            ;;
        -vv)
            verbose=2
            shift
            ;;
        -vvv)
            verbose=3
            shift
            ;;
        *)
            dirs+=("$1")
            shift
            ;;
    esac
done

if [ "${#dirs[@]}" -gt 1 ]; then
    printf "%s" "Method"
    for dir in "${dirs[@]}"; do
        printf "\t%s" "$dir"
    done
    printf "\t%s\n" "URI"
else
    echo -e "Method\tCode\tURI"
fi
echo "====================================================================="

scripts=()
for script in "${dirs[0]}"/*; do
    [ -f "$script" ] && scripts+=("$(basename "$script")")
done
scripts=($(printf "%s\n" "${scripts[@]}" | sort -V))

for script in "${scripts[@]}"; do
    codes=()
    method=""
    uri=""
    short_uri=""
    for dir in "${dirs[@]}"; do
        script="$dir/$(basename "$script")"
        if [ ${#filter[@]} -gt 0 ]; then
            match=false
            for f in "${filter[@]}"; do
                if [[ "$script" != *"$f"* ]]; then
                    match=true
                    break
                fi
            done
            if [ "$match" = false ]; then
                continue
            fi
        fi
        if [ -f "$script" ]; then
            output=$(bash "$script" 2>&1)

            m=$(echo "$output" | grep "^>" | grep "HTTP" | awk '{print $2}')
            method=${m:-$method}
            u="/"$(echo "$output" | grep "^>" | grep "HTTP" | awk '{print $3}' | cut -d'/' -f4-)
            uri=${u:-$uri}
            code=$(echo "$output" | grep "^< HTTP" | awk '{print $3}')
            codes+=("$code")
            body=$(echo "$output" | awk 'NF && !/^[*><]/' | tail -1)
            short_body=$(echo "$body" | cut -c1-70)
            suri=$(echo "$uri" | cut -c1-40)
            short_uri=${suri:-$short_uri}
            length=$(echo -n "$body" | wc -c)

            sleep "$delay"

            if [ "${#dirs[@]}" -gt 1 ]; then
                continue
            fi

            if [ -n "$method" ] && [ -n "$code" ]; then
                if [[ "$script" == *idor* || "$script" == *sqli* ]]; then
                    printf "${LIGHT_GRAY}\t%s\t%s\t%s${NC}\n" "$code" "$uri" "$length"
                else
                    if [ "$verbose" -eq 0 ]; then
                        echo -e "$method\t$code\t$short_uri"
                    else
                        echo -e "$method\t$code\t$uri"
                    fi
                fi

                if [ "$verbose" -ge 1 ]; then
                    echo -e "\t$short_body"
                fi
                if [ "$verbose" -ge 2 ]; then
                    echo -e "\t$body"
                fi
                if [ "$verbose" -ge 3 ]; then
                    echo "======$script======"
                    echo -e "\t$output"
                fi
            else
                echo "$output"
            fi
        fi
    done
    if [ "${#dirs[@]}" -gt 1 ]; then
        if [ -n "$method" ] && [ -n "$code" ]; then
            printf "%s" "$method"

            first="${codes[0]}"
            all_same=true
            for code in "${codes[@]}"; do
                [ "$code" != "$first" ] && all_same=false
            done

            for code in "${codes[@]}"; do
                if [ "$all_same" = true ]; then
                    printf "\t${GREEN}%s${NC}" "$code"
                else
                    printf "\t${RED}%s${NC}" "$code"
                fi
            done
            
            if [ "$verbose" -eq 0 ]; then
                printf "\t\t%s\n" "$short_uri"
            else
                printf "\t\t%s\n" "$uri"
            fi
        fi
    fi
done
