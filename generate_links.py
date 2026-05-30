import pickle
import os
import warnings
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from scraper.fetcher import Fetcher

warnings.filterwarnings("ignore", category=DeprecationWarning)

subforums = { # Page numbers as of 30.05.2026
    "must_read": {"url": "https://incels.is/forums/must-read-content.23/", "pages": 4},
    "off_topic": {"url": "https://incels.is/forums/the-lounge.4/", "pages": 2795},
    "inceldom": {"url": "https://incels.is/forums/inceldom-discussion.2/", "pages": 3854}
}

def scrape_link_list(forum_url, n_pages, fetcher):
    return_links = []
    
    for i in tqdm(range(1, n_pages + 1), unit="page"):
        url_r = f"{forum_url}page-{i}"
        html = fetcher.get_html(url_r)
        if not html:
            continue
            
        soup = bs(html, "html.parser")
        threads = soup.find_all("div", {"class": "structItem--thread"})
        
        for t in threads:
            try:
                title_div = t.find("div", {"class": "structItem-title"})
                base_link = title_div.findAll("a")[-1].get('href')
                
                max_pages_html = t.find("span", {"class": "structItem-pageJump"})
                max_pages = int(max_pages_html.findAll("a")[-1].text) if max_pages_html else 1
                
                for k in range(1, max_pages + 1):
                    return_links.append(f"{base_link}page-{k}")
            except Exception as e:
                print(f"\nError while parsing thread on page: {i}: {e}")
                continue
    return return_links

def main():
    fetcher = Fetcher()
    os.makedirs("links", exist_ok=True)
    
    for forum_key, config in subforums.items():
        print(f"Generating links for subforum: {forum_key}")
        links = scrape_link_list(config["url"], config["pages"], fetcher)
    
        output_path = f"links/{forum_key}.pkl"
        with open(output_path, 'wb') as f:
            pickle.dump(links, f)
        
        print(f"Done! {len(links)} links saved in '{output_path}'")

if __name__ == "__main__":
    main()