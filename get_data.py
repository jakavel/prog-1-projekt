import requests
import pathlib
import helpers
import random
import csv

def save_page(p: int,  ignore_saved: bool=False) -> bool:
    """Saves the p^th page cotaining a list of 30 mods, returns True if a request was made, False otherwise."""
    save_location = pathlib.Path().parent / "data" / "lists" / f"page_{p}.html"
    if save_location.exists() and not ignore_saved:
        # don't save page if it already has a file
        return False

    base_params = {
        "appid": 394360,
        "browsesort": "trend",
        # "section": ,
        "actualsort": "trend",
        "p": p,
        "days": -1,
    }

    return save_something("https://steamcommunity.com/workshop/browse/", base_params, save_location)

def save_entry(entry_id: int,  ignore_saved: bool=False) -> bool:
    """Saves the entry for the mod if entry_id, returns True if a request was made, False otherwise."""
    save_location = pathlib.Path().parent / "data" / "entries" / f"entry_{entry_id}.html"
    if save_location.exists() and not ignore_saved:
        # don't save page if it already has a file
        return False

    base_params = {
        "id": entry_id,
    }

    return save_something("https://steamcommunity.com/sharedfiles/filedetails/", base_params, save_location)

def save_something(url: str, params: str, save_location: pathlib.Path, depth: int=0) -> bool:
    try:
        ans = requests.get(
            url,
            params,
        )
    except requests.exceptions.ConnectionError:
        # wait for a bit and try again
        if depth > 10:
            raise RuntimeError(f"Could not get response from {url}, {params}")
        wait_time = 180
        print("\nGot a ConnectionError from {url}, {params}, waiting for {wait_time}s and trying again.")
        time.sleep(wait_time)
        return save_page(url, params, save_location, depth=depth+1)

    if ans.status_code != 200:
        print(f"\nResponse to {url}, {params} gave code {ans.status_code}, skipping")
        with open("skipped.txt", "a", encoding="utf-8", newline="") as skipped_list:
            skipped_writer = csv.writer(skipped_list)
            skipped_writer.writerow(
                [url, params, ans.status_code]
            )
    else:
        with open(save_location, "w", encoding="utf-8") as location_html:
            location_html.write(ans.text)
    return True

def get_needed(thing: str) -> list[int]:
    needed_things = []
    location = pathlib.Path().parent / "data" / f"{thing}_needed.txt"
    with open(location, "r") as needed:
        for line in needed:
            if line.strip().isdigit():
                needed_things.append(int(line.strip()))
            else:
                print(f"Cannot read line '{line}' in data/lists_needed.txt")
        if len(needed_things) == 0:
            print("Exiting, no page numbers are maked as needed.")
            exit()
    return needed_things

def save_things(delay: int, saver_function, thing: str, message: str="", break_interval: int=1000):
    needed_things = get_needed(thing)
    print(f"{message}, saving {len(needed_things)} things, expected time: {helpers.nice_time(delay * len(needed_things))}")
    saved = 0
    for i, page_id in enumerate(needed_things):
        if saver_function(page_id):
            saved += 1
            helpers.random_sleep(delay)
        if break_interval > 0:
            # negative break_interval means don't take any breaks
            if saved % break_interval == 0 and saved > 0:
                answer = input(f"\nTaking a break after {saved} things, continue? Y/n ")
                if answer.lower() not in ("y", "yes", ""):
                    break
        helpers.print_progress(i, len(needed_things) - 1, name=message, delay=delay)


if __name__ == "__main__":
    save_things(2, save_page, "lists", message="Fetching pages")
    save_things(3, save_entry, "entries", message="Downloading entries", break_interval=-1)

