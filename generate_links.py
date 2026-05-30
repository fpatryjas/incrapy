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

def parse_thread_activity(time_tag):
    if not time_tag:
        return None

    unix_timestamp = time_tag.get("data-time")
    if unix_timestamp:
        try:
            return datetime.fromtimestamp(int(unix_timestamp), timezone.utc)
        except (TypeError, ValueError, OSError):
            pass

    datetime_value = time_tag.get("datetime")
    if datetime_value:
        try:
            parsed_datetime = datetime.fromisoformat(
                datetime_value.replace("Z", "+00:00")
            )
            if parsed_datetime.tzinfo is None:
                return parsed_datetime.replace(tzinfo=timezone.utc)
            return parsed_datetime.astimezone(timezone.utc)
        except ValueError:
            pass

    return None

def get_thread_activity(thread):
    thread_activities = []
    for time_tag in thread.find_all("time"):
        parsed_activity = parse_thread_activity(time_tag)
        if parsed_activity is not None:
            thread_activities.append(parsed_activity)
    return max(thread_activities) if thread_activities else None


def format_thread_activity(thread_activity):
    if thread_activity is None:
        return None
    return thread_activity.isoformat(timespec="seconds")


def is_in_date_range(thread_activity, start_date, end_date):
    if thread_activity is None:
        return True

    thread_date = thread_activity.date()
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
        page_activities = []

        for t in threads:
            thread_activity = get_thread_activity(t)
            if thread_activity is not None:
                page_activities.append(thread_activity)

            if not is_in_date_range(thread_activity, start_date, end_date):
                continue

            try:
                title_div = t.find("div", {"class": "structItem-title"})
                base_link = title_div.findAll("a")[-1].get("href")

                max_pages_html = t.find("span", {"class": "structItem-pageJump"})
                max_pages = (
                    int(max_pages_html.findAll("a")[-1].text)
                    if max_pages_html
                    else 1
                )

                formatted_thread_activity = format_thread_activity(thread_activity)
                for k in range(1, max_pages + 1):
                    return_links.append(
                        (f"{base_link}page-{k}", formatted_thread_activity)
                    )
            except Exception as e:
                print(f"\nError while parsing thread on page: {i}: {e}")
                continue

        if (
            start_date
            and page_activities
            and max(page_activities).date() < start_date
        ):
            newest_activity = max(page_activities)
            print(
                f"Stopping at page {i}: "
                f"Newest thread date {newest_activity:%d.%m.%Y} is before {start_date:%d.%m.%Y}."
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