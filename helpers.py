import time
import random


def print_progress(done: int, total: int, name: str="", delay: int=-1) -> None:
    WIDTH = 30
    fullness = "-"
    emptyness = " "
    border = ">"

    progress = done / total
    full = round(WIDTH * progress)
    empty = WIDTH - full - len(border)

    newline_maybe = "\n" if done == total else ""

    if name != "":
        name = name + " "

    if delay == -1:
        finisher = f"round(progress * 100, 1)%"
    else:
        finisher = f"{nice_time((total - done) * delay)} left    "

    print(f"\r{name}[{full * fullness}{border}{empty * emptyness}] {finisher}", end=newline_maybe)


def random_sleep(average_time: int) -> None:
    time.sleep((1.5 - random.random()) * average_time)


def nice_time(seconds: int) -> str:
    time = {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}
    if seconds >= 24 * 60 * 60:
        time["days"] = seconds // (24 * 60 * 60)
        seconds %= 24 * 60 * 60
    if seconds >= 60 * 60:
        time["hours"] = seconds // (60 * 60)
        seconds %= 60 * 60
    if seconds >= 60:
        time["minutes"] = seconds // 60
        seconds %= 60
    time["seconds"] = seconds

    return (
           (f"{time['days']} d " if time["days"] > 0 else "") +
           (f"{time['hours']} h " if time["hours"] > 0 else "") +
           (f"{time['minutes']} m " if time["minutes"] > 0 else "") +
           (f"{time['seconds']} s" if time["seconds"] > 0 else "0 s")
    )
