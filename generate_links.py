import pickle
import os
import warnings
from datetime import datetime, timezone
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from scraper.fetcher import Fetcher

warnings.filterwarnings("ignore", category=DeprecationWarning)

date_format = "%d.%m.%Y"
startdate = None
enddate = None

subforums = { # Page numbers as of 30.05.2026
    "must_read": {"url": "https://incels.is/forums/must-read-content.23/", "pages": 4},
    "off_topic": {"url": "https://incels.is/forums/the-lounge.4/", "pages": 2795},
    "inceldom": {"url": "https://incels.is/forums/inceldom-discussion.2/", "pages": 3854}
}

def parse_date_filter(date_value, variable_name):
    if date_value in (None, ""):
        return None

    try:
        return datetime.strptime(date_value, date_format).date()
    except ValueError as e:
        raise ValueError(
            f"Invalid date in {variable_name}: {date_value!r}. "
            "Expected format is DD.MM.YYYY"
        ) from e

def parse_thread_date(time_tag):
    if not time_tag:
        return None

    unix_timestamp = time_tag.get("data-time")
    if unix_timestamp:
        try:
            return datetime.fromtimestamp(int(unix_timestamp), timezone.utc).date()
        except (TypeError, ValueError, OSError):
            pass

    datetime_value = time_tag.get("datetime")
    if datetime_value:
        try:
            return datetime.fromisoformat(datetime_value.replace("Z", "+00:00")).date()
        except ValueError:
            pass

    return None

def get_thread_date(thread):
    thread_dates = []
    for time_tag in thread.find_all("time"):
        parsed_date = parse_thread_date(time_tag)
        if parsed_date is not None:
            thread_dates.append(parsed_date)
    return max(thread_dates) if thread_dates else None

def format_thread_activity(thread_date):
    return thread_date.strftime(date_format) if thread_date is not None else None

def is_in_date_range(thread_date, start_date, end_date):
    if thread_date is None:
        return True
    if start_date and thread_date < start_date:
        return False
    if end_date and thread_date > end_date:
        return False
    return True

def scrape_link_list(forum_url, n_pages, fetcher, start_date=None, end_date=None):
    return_links = []

    for i in tqdm(range(1, n_pages + 1), unit="page"):
        url_r = f"{forum_url}page-{i}"
        html = fetcher.get_html(url_r)
        if not html:
            continue

        soup = bs(html, "html.parser")
        threads = soup.find_all("div", {"class": "structItem--thread"})
        page_dates = []

        for t in threads:
            thread_date = get_thread_date(t)
            if thread_date is not None:
                page_dates.append(thread_date)

            if not is_in_date_range(thread_date, start_date, end_date):
                continue

            try:
                title_div = t.find("div", {"class": "structItem-title"})
                base_link = title_div.findAll("a")[-1].get('href')

                max_pages_html = t.find("span", {"class": "structItem-pageJump"})
                max_pages = int(max_pages_html.findAll("a")[-1].text) if max_pages_html else 1

                thread_activity = format_thread_activity(thread_date)
                for k in range(1, max_pages + 1):
                    return_links.append((f"{base_link}page-{k}", thread_activity))
            except Exception as e:
                print(f"\nError while parsing thread on page: {i}: {e}")
                continue

        if start_date and page_dates and max(page_dates) < start_date:
            newest_date = max(page_dates)
            print(
                f"Stopping at page {i}: "
                f"Newest thread date {newest_date:%d.%m.%Y} is before {startdate}."
            )
            break

    return return_links

def main():
    start_date = parse_date_filter(startdate, "startdate")
    end_date = parse_date_filter(enddate, "enddate")
    if start_date and end_date and start_date > end_date:
        raise ValueError("startdate must not be after enddate.")

    fetcher = Fetcher()
    os.makedirs("links", exist_ok=True)

    for forum_key, config in subforums.items():
        print(f"Generating links for subforum: {forum_key}")
        links = scrape_link_list(
            config["url"],
            config["pages"],
            fetcher,
            start_date,
            end_date,
        )

        output_path = f"links/{forum_key}.pkl"
        with open(output_path, 'wb') as f:
            pickle.dump(links, f)
        
        print(f"Done! {len(links)} links saved in '{output_path}'")

if __name__ == "__main__":
    main()