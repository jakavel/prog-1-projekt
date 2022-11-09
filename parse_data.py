import dataclasses
import re
import pathlib
import csv


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


def get_entry_htmls() -> list[str]:
    location = pathlib.Path().parent / "data" / "entries"
    for file in location.iterdir():
        with open(file, "r", encoding="utf-8") as html:
            # yield, da ne naloži vseh strani na enkrat v spomin, ker ima moj
            # laptop samo 4 GB spomina
            yield file, html.read()


def find_exactly_one(regex: re.Pattern, text: str) -> str:
    found = list(regex.finditer(text))
    assert len(found) == 1
    return found[0]


TITLE = re.compile(r"""<div class="workshopItemTitle">(?P<title>.*?)</div>""")
def get_title_from_entry(entry: str) -> str:
    global TITLE
    return find_exactly_one(TITLE, entry).group("title")


STATS = re.compile(\
                   r"""\s*<table class="stats_table">\s*(<tbody>)?\s*<tr>\s*<td>(?P<visitors>[\d,]+)</td>\s*"""
                   r"""<td>Unique Visitors</td>\s*</tr>\s*<tr>\s*<td>(?P<subscribers>[\d,]+)</td>\s*"""
                   r"""<td>Current Subscribers</td>\s*</tr>\s*<tr>\s*<td>(?P<favorites>[\d,]+)</td>"""
                   r"""\s*<td>Current Favorites</td>\s*</tr>\s*(</tbody>)?\s*</table>"""
                  )
def get_stats_from_entry(entry: str) -> tuple[int, int, int]:
    global STATS
    """Vrne tuple, ki predstavlja (# ogledov, # nalaganj, # všečkov)"""
    rezultat = find_exactly_one(STATS, entry)
    return (  # vsaka 3 števila je vstavljena vejica
        int(rezultat.group("visitors").replace(",", "")),
        int(rezultat.group("subscribers").replace(",", "")),
        int(rezultat.group("favorites").replace(",", "")),
     )


RATING_IMAGE = {
    '1-star_large.png?v=2': 1.0,
    '2-star_large.png?v=2': 2.0,
    '3-star_large.png?v=2': 3.0,
    '4-star_large.png?v=2': 4.0,
    '5-star_large.png?v=2': 5.0,
    'not-yet_large.png?v=2': float("nan"),
}
RATING = re.compile(\
                    r"""<div class="ratingSection">\s*<div class="fileRatingDetails">"""
                    r"""<img src="https://community.cloudflare.steamstatic.com/public/images/sharedfiles/"""
                    r"""(?P<image>.*?)" /></div>\s*(<div class="numRatings">)?\s*(?P<rating>.*?)\s*(ratings?)?\s*</div>\s*</div>"""
                   )
def get_score_from_entry(entry: str) -> float:
    global RATING_IMAGE, RATING
    found = find_exactly_one(RATING, entry)

    assert found.group("image") in RATING_IMAGE

    if found.group("rating") == "Not enough":
        num_of_ratings = 0
    else:
        num_of_ratings = int(found.group("rating").replace(",", ""))

    return RATING_IMAGE[found.group("image")], num_of_ratings


AUTHOR = re.compile(r"""<div class="friendBlockContent">\s*(?P<author>.*?)<br>"""
                    r"""\s*<span class="friendSmallText">\s*.*?\s*</span>\s*</div>""")
def get_authors_from_entry(entry: str) -> list[str]:
    authors_iter = AUTHOR.finditer(entry)
    authors_list = []
    for author in authors_iter:
        authors_list.append(author.group("author"))
    assert len(authors_list) >= 1
    return authors_list


SIZE = re.compile(r"""<div class="detailsStatsContainerRight">\s*<div class="detailsStatRight">(?P<size>.*?)</div>""")
def get_size_from_entry(entry: str) -> int:
    global SIZE
    size_str = find_exactly_one(SIZE, entry).group("size")
    return round(
        float(size_str.replace("MB", "").replace(",", "")) * ( 2 ** 20 )
    )


TAG = re.compile(r"""<a href="https://steamcommunity.com/workshop/browse/\?appid=394360&browsesort=toprated&section=readytouseitems&requiredtags%5B%5D=.*?">(?P<tag>.*?)</a>""")
def get_tags_from_entry(entry: str) -> list[str]:
    tags_iter = TAG.finditer(entry)
    tags_list = []
    for tag in tags_iter:
        tags_list.append(tag.group("tag"))
    # tu ni asserta, ker imajo neki modi 0 tagov
    return tags_list


ID_INPUT = re.compile(r"""<input type="hidden" name="id" value="(?P<id>\d+)" \/>""")
def get_id_from_entry(entry: str) -> int:
    global ID_INPUT
    # sta dve skriti input polji z id-jem, ne sesuj se, če najdeš oba
    return ID_INPUT.search(entry).group("id")
    return 1


def write_main_csv(*columns):
    locaton = pathlib.Path().parent / "data" / "parsed" / "mods.csv"
    for col in columns:
        # vsi seznami atributov so enake dolžine
        assert len(col) == len(columns[0])
    # seznamov je toliko, kot je imen
    names = ["id", "title", "views", "downloads", "likes", "rating", "number_of_ratings", "size"]
    assert len(names) == len(columns)
    with open(locaton, "w", newline='', encoding="utf-8") as csv_file:
        mod_writer = csv.writer(csv_file)
        mod_writer.writerow(names)
        for new_row in zip(*columns):
            mod_writer.writerow(new_row)


def write_new_table(things: list[list[str]], name_singular: str, name_plural: str) -> dict:
    id_dict = dict()
    locaton = pathlib.Path().parent / "data" / "parsed" / f"{name_plural}.csv"
    unique_things = set()
    for things_of_mod in things:
        for thing in things_of_mod:
            unique_things.add(thing)
    with open(locaton, "w", newline='', encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([f"{name_singular}_id", f"{name_singular}_name"])
        for i, thing in enumerate(sorted(unique_things)):
            writer.writerow([i, thing])
            id_dict[thing] = i
    return id_dict


def write_thing_mod_table(ids: list[int], things: list[list[str]], id_dict: dict, name_singular: str) -> None:
    locaton = pathlib.Path().parent / "data" / "parsed" / f"{name_singular}_mod.csv"
    with open(locaton, "w", newline='', encoding="utf-8") as csv_file:
        thing_mod_writer = csv.writer(csv_file)
        thing_mod_writer.writerow(["mod_id", f"{name_singular}_id"])
        for mod_id, things_of_mod in zip(ids, things):
            for one_thing in things_of_mod:
                thing_mod_writer.writerow([mod_id, id_dict[one_thing]])


if __name__ == "__main__":
    mods = get_mods_from_pages()
    print(f"Found {len(mods)} mods, parsing...")
    mark_needed_entries(mods)

    problems = []

    titles = []
    views = []
    downloads = []
    likes = []
    ratings = []
    num_ratings = []
    authors = []
    sizes = []
    tags = []
    ids = []

    prev_len = len(tags)

    for i, (file, entry) in enumerate(get_entry_htmls()):
        try:
            titles.append(get_title_from_entry(entry))
            view, download, like = get_stats_from_entry(entry)
            views.append(view)
            downloads.append(download)
            likes.append(like)
            r, n = get_score_from_entry(entry)
            ratings.append(r)
            num_ratings.append(n)
            authors.append(get_authors_from_entry(entry))
            sizes.append(get_size_from_entry(entry))
            tags.append(get_tags_from_entry(entry))
            ids.append(get_id_from_entry(entry))
        except AssertionError:
            if file not in problems:
                problems.append(file)

    write_main_csv(
        ids,
        titles,
        views,
        downloads,
        likes,
        ratings,
        num_ratings,
        sizes,
    )

    tag_dict = write_new_table(tags, "tag", "tags")
    write_thing_mod_table(ids, tags, tag_dict, "tag")

    author_dict = write_new_table(authors, "author", "authors")
    write_thing_mod_table(ids, authors, author_dict, "author")

    # 21 od datotek je samo stran, kjer piše da je te strani ni bilo mogoče naložiti
    # ( tudi, če jih poberem še enkrat, najbrš kakšna napaka na Steamovi strani )
    print(f"Failed to parse {len(problems)} files")

