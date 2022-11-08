import dataclasses
import re
import pathlib


def mods_from_page(page: str):
    mod_regex = re.compile(
        r'<a data-panel="{&quot;focusable&quot;:false}" href="https://steamcommunity.com/sharedfiles/filedetails/\?id=(?P<id>\d+)&searchtext=" class="item_link"><div class="workshopItemTitle ellipsis">(?P<name>.+?)</div></a>'
    )
    for mod in mod_regex.finditer(page):
        yield (mod.group("id"), mod.group("name"))


def get_page(p: int):
    locaton = pathlib.Path().parent / "data" / "lists" / f"page_{p}.html"
    if locaton.exists():
        with open(locaton, "r", encoding="utf-8") as page_file:
            return page_file.read()
    else:
        return False

def get_mods_from_pages() -> list[tuple[str, str]]:
    count = 1
    mods = []
    while (page := get_page(count)):
        count += 1
        for mod in mods_from_page(page):
            mods.append(mod)
    return mods


def mark_needed_entries(mods):
    location = pathlib.Path().parent / "data" / "entries_needed.txt"
    already_written = set()
    if location.exists():
        with open(location, "r", encoding="utf-8") as entries_file:
            for line in entries_file:
                already_written.add(line.strip())

    with open(location, "a", encoding="utf-8") as entries_file:
        for mod_id, mod_name in mods:
            if not mod_id in already_written:
                entries_file.write(mod_id + "\n")


if __name__ == "__main__":
    mods = get_mods_from_pages()
    print(f"Found {len(mods)} mods, saving...")
    mark_needed_entries(mods)
