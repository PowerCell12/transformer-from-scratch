import json
import os 
import html 
import unicodedata
import strip_markdown
import re 
from concurrent.futures import ProcessPoolExecutor
from itertools import batched

def replace_PII(line):
    replaced_emails = re.sub(
        r"\b[a-zA-Z0-9+_-]+(?:\.[a-zA-Z0-9+_-]+)*@[^\s@\.]+(?:\.[a-zA-Z0-9-]{1,})*\.[a-zA-Z]{2,}", 
        "[EMAIL]", 
        line
    )        

    replaced_usernames = re.sub(
        r"\bu\/[a-zA-Z0-9_\-]{3,20}(?![\w\-])",
        "[USERNAME]",
        replaced_emails
    )

    return replaced_usernames

def replace_newlines(line):
    paragraph_break_collapse = re.sub(r"[ \t]{0,}\n(?:[ \t]*\n){2,}[ \t]{0,}", "\n\n", line)

    single_space_removal = re.sub(r"(?<!\n)\n{1}(?!\n)", " ", paragraph_break_collapse)

    runs_of_spaces_tabs_removal = re.sub(r"[ \t]{2,}", " ", single_space_removal)

    trimmed = runs_of_spaces_tabs_removal.strip()

    return trimmed

def clean(data):
    batch = []

    for line in data:
        try:
            fixed_line = json.loads(line)['text']

            unescaped_data = html.unescape(fixed_line)

            unicode_normalized = unicodedata.normalize("NFKC", unescaped_data)

            stripped_markdown = strip_markdown.strip_markdown(unicode_normalized)

            replaced_URLs = re.sub(
                r"\b(?:(?:https?|ftp)://[^\s/$.?#]+\.[^\s$/?#<>]{1,}|(?:(?:https?|ftp)://)?localhost)(?::\d+)?(?:[/?#][^\s]*)?[\w/~+=&#-]", 
                "[URL]", 
                stripped_markdown
            )

            replaced_PII = replace_PII(replaced_URLs)

            replaced_newlines = replace_newlines(replaced_PII)

            batch.append(json.dumps({"text": replaced_newlines}))
        except Exception as ex:
            print(ex)
            ## add logging (message + count). Right now don't know if a run is bad.

    return batch 

if __name__ == "__main__":        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pathToMainDirectory = "/".join(current_dir.split("/")[:-1])

    files = os.listdir(f"{pathToMainDirectory}/data/filtered_data")

    for file in files: 

        if file.endswith(".jsonl"):

            with open(f"{pathToMainDirectory}/data/filtered_data/{file}", mode="r", encoding="utf-8") as opened_file:
                batched_file = batched(opened_file, n=10_000)

                cleaned_data_file_path=f"{pathToMainDirectory}/data/cleaned_data/{file}"
                
                with open(cleaned_data_file_path, mode="w", encoding="utf-8") as cleaned_data:                    

                    with ProcessPoolExecutor(max_workers=4) as executor:
                        results = executor.map(clean, batched_file)  

                        for result in results:
                            for datum in result:
                                cleaned_data.write(datum + '\n')       
