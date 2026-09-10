#!/bin/bash
set -euo pipefail

pathToMainDirectory="$(readlink -f "$(dirname "${BASH_SOURCE[0]}")"/../..)"

source "${pathToMainDirectory}/.env"

pathToJobLog="${pathToMainDirectory}/data/filtered_data/"
pathToPostsJSON="${pathToMainDirectory}/data/filtered_data/posts.jsonl"
pathToCommentsJSON="${pathToMainDirectory}/data/filtered_data/comments.jsonl"

subreddits=("CredibleDefense" "WarCollege" "geopolitics" "energy" 
            "nuclear" "RenewableEnergy" "PowerSystems" "programming"
            )

grepSubreddits=$(printf "%s|" "${subreddits[@]}" | sed 's/|$//')
selectSubreddits=$(printf "%s\n" "${subreddits[@]}" | jq -R . | jq -s . | jq -c .)

export grepSubreddits
export selectSubreddits

: > "${pathToPostsJSON}"
: > "${pathToCommentsJSON}"

extract_data_body () {
            zstd -dc --long=31 "$1" | grep -Ew "\"subreddit\":\"(${grepSubreddits})\"" |
            jq -c \
             --argjson selectSubreddits "${selectSubreddits}" \
             --argjson scoreValue "${scoreValue}" \
             --arg InfoFieldName "${InfoFieldName}" \
             --argjson InfoFieldLength "${InfoFieldLength}" '
                select(
                    (.subreddit | IN($selectSubreddits[]))
                    and .score > $scoreValue
                    and (.[$InfoFieldName] | IN("", "[deleted]", "[removed]") | not)
                    and .author != "AutoModerator" 
                    and ((.[$InfoFieldName] | length) > $InfoFieldLength)
                ) 
                | {text: (if .title != null then "\(.title) \(.[$InfoFieldName])" else "\(.[$InfoFieldName])" end)}
            '
}

export -f extract_data_body

extract_data () {
    export pathToDirectory="$1" 
    export InfoFieldName="$2"
    export scoreValue="$3"
    export InfoFieldLength="$4"
    export pathToJson="$5"

    IFS="/" read -r -a jsonNameArray <<< "${pathToJson}"

    jsonName="${jsonNameArray[-1]/.jsonl/JobLog.tsv}"

    find "${pathToDirectory}" -name "*.zst" | parallel --joblog "${pathToJobLog}${jsonName}" --line-buffer --retries 1  -j 3 extract_data_body {} >> "${pathToJson}"
}

extract_data "${pathToPosts}" 'selftext' 10 150 "${pathToPostsJSON}"

extract_data "${pathToComments}" 'body' 5 20 "${pathToCommentsJSON}"

echo "Finished the extraction from Reddit posts!"