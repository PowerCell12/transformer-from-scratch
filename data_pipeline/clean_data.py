import json
import os 
import html 
import unicodedata
import strip_markdown
import re 
from concurrent.futures import ProcessPoolExecutor
from itertools import batched
import multiprocessing

def set_queue(q):
    global shared_queue
    shared_queue = q

def write_data(file_path):

    with open(file_path, mode="w", encoding="utf-8") as write_to_file:
        write_to_file.truncate(0)

        try:        
            while True:
                items = shared_queue.get()

                if (items is None):
                    break

                write_to_file.writelines(item + "\n" for item in items)

        except Exception as ex:
            print(ex)
            ## Add real logging here

            raise    

def clean(data):
    batch = []

    for line in data:

        try:
            fixed_line = json.loads(line)['text']

            unescaped_data = html.unescape(fixed_line)

            unicode_normalized = unicodedata.normalize("NFKC", unescaped_data)

            stripped_markdown = strip_markdown.strip_markdown(unicode_normalized)

            fixed_URLs = re.sub("(?:https?://|www\\.)[^\\s/$.?#].[^\\s]*", "[URL]", stripped_markdown)

            paragraph_break_collapse = re.sub("[ \t]{0,}\n(?:[ \t]*\n){2,}[ \t]{0,}", "\n\n", fixed_URLs)

            single_space_removal = re.sub("(?<!\n)\n{1}(?!\n)", " ", paragraph_break_collapse)

            runs_of_spaces_tabs_removal = re.sub("[ |\t]{2,}", " ", single_space_removal)

            trimmed = runs_of_spaces_tabs_removal.strip()

            batch.append(json.dumps({"text": trimmed}))

            if len(batch) == 100:
                shared_queue.put(batch)
                batch = []

        except Exception as ex:
            print(ex)
            ## add logging (message + count)

    if batch:
        shared_queue.put(batch)

if __name__ == "__main__":        
    multiprocessing.set_start_method("forkserver") # doesn't work for windows

    current_dir = os.path.dirname(os.path.abspath(__file__))
    pathToMainDirectory = "/".join(current_dir.split("/")[:-1])

    files = os.listdir(f"{pathToMainDirectory}/data/filtered_data")

    shared_queue = multiprocessing.Queue(maxsize=200)

    for file in files: 

        if file.endswith(".jsonl"):

            with open(f"{pathToMainDirectory}/data/filtered_data/{file}", mode="r", encoding="utf-8") as opened_file:
                batched_file = batched(opened_file, n=40_000)

                with ProcessPoolExecutor(max_workers=4, initializer=set_queue, initargs=(shared_queue,)) as executor:

                    write_to_file = executor.submit(
                        write_data, 
                        file_path=f"{pathToMainDirectory}/data/cleaned_data/{file}"
                    )

                    results = executor.map(clean, batched_file)  

                    for result in results:
                            ...

                    shared_queue.put(None)  

                    write_to_file.result()