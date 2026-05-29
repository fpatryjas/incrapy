import pickle
from tqdm import tqdm
from scraper.orchestrator import ForumOrchestrator

def main():
    orchestrator = ForumOrchestrator()
    
    to_scrape = ["must_read", "off_topic", "inceldom"]

    for i in to_scrape:
        links = f"links/{i}.pkl"

        with open(links, 'rb') as f:
            links_to_scrape = pickle.load(f)

        print(f"Scraping {len(links_to_scrape)} pages from '{i}'...")
    
        for link in tqdm(links_to_scrape, unit="page"):
            success = orchestrator.scrape_single_page(link, i)
            if not success:
                tqdm.write(f"Error when scraping: {link}")

        print("Scraping done!")

    if orchestrator.faulty_links:
        print(f"This link did not work: {orchestrator.faulty_links}")

    orchestrator.close()

if __name__ == "__main__":
    main()