## `Incrapy` – Python-based scraper of the `incels.is` web forum

The goal of this repository is a clean re-implementation of the [`inside_incels.is`](https://github.com/lionwedel/inside_incels.is) web scraper by [@lionwedel](https://github.com/lionwedel) using Python.

---

### How to use this scraper

**1. Run `generate_links.py`**

This effectivly iterates through the selected subforum (by default: _Inceldom Discussion_) and saves the link of every thread. Specify `startdate` and `enddate` if you wish to limit the data based on recent thread activity (format: _DD.MM.YYYY_). If you keep both at _None_, everything is going to be scraped.

```
startdate = "29.05.2026"
enddate = "30.05.2026"
```

Before running, check the selected subforum by hand, because you might have to update the total number of pages.

```
subforums = { # Page numbers as of 31.05.2026
    "inceldom": {"url": "https://incels.is/forums/inceldom-discussion.2/", "pages": 3855}
}
```

> [!NOTE]  
> It is possible to scrape multiple subforums simultaneously!

This generates a list with the fetched thread links inside `links/inceldom.pkl`, which is the basis for the upcoming step.

---

**2. Run `main.py`**

This takes the previously generated link list and scrapes the content of each thread, storing everything within an SQLite database inside `data/forum.db`. Depending on what subforum you scrape, you might have to adapt `to_scrape` according to the specific name of the subforum (by default: _inceldom_).

```
to_scrape = ["inceldom"] # (e.g. "must_read" or "off_topic")
```

A change here also makes it necessary to change `scraper/database.py` in order to create a correctly named table.

```
tables = ["inceldom"] # (e.g. "must_read" or "off_topic")
```

> [!NOTE]  
> It is possible to scrape multiple subforums simultaneously!

Once both is done, you might execute the script and wait until the process is finished, it might take some time depending on the total volume to scrape.

---

**3. Run `load_data.py`**

This basically takes the scraped data from `data/forum.db` and loads it into a dataframe. It saves the dataframe into `data/forum_raw.pkl` and `data/forum_json.pkl`, consisting of the following schema below.

```
title           TEXT
thread_id        INT
latest_activity TEXT
user_id          INT
user_name       TEXT
user_title      TEXT
rank            TEXT
n_stars          INT
date            TEXT
n_posts          INT
time_online     TEXT
datetime        DATE
n_post           INT
message         TEXT
quote_host      TEXT
quote_url       TEXT
quoted_user     TEXT
qu_id           TEXT
```

Before saving, the data is ordered descending by the `latest_activity` timestamp variable, making it easier to go through later.

---