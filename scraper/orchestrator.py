from bs4 import BeautifulSoup as bs
from scraper.fetcher import Fetcher
from scraper.parser import Parser
from scraper.database import DatabaseManager
from scraper.config import forum, selectors

class ForumOrchestrator:
    def __init__(self):
        self.fetcher = Fetcher()
        self.parser = Parser()
        self.db = DatabaseManager()
        self.faulty_links = []

    def scrape_single_page(self, url_path, table_name, thread_activity=None):
        full_url = url_path if url_path.startswith("http") else f"{forum}{url_path}"
        
        html = self.fetcher.get_html(full_url)
        if not html:
            self.faulty_links.append(url_path)
            return False

        soup = bs(html, "html.parser")

        try:
            title_tag = soup.select_one(selectors["title"])
            title = self.parser.clean_text(title_tag.text) if title_tag else "Unknown Title"
            
            thread_type = self.parser.get_thread_type(soup)
            
            if thread_type == 1:
                posts = self.parser.parse_comments(soup, title, table_name, thread_id=0, thread_activity=thread_activity)
                for post in posts:
                    self.db.insert_post(table_name, post)
            
            elif thread_type == 0:
                message_blocks = soup.select(selectors["thread_blocks"])
                op_block = message_blocks[0]
                
                op_data = self.parser.scrape_op(op_block, thread_activity=thread_activity)
                if op_data:
                    full_op_data = tuple([title] + op_data)
                    self.db.insert_post(table_name, full_op_data)
                    
                    posts = self.parser.parse_comments(message_blocks[1], title, table_name, thread_id=op_data[0], thread_activity=thread_activity)
                    for post in posts:
                        self.db.insert_post(table_name, post)
            
            return True
        except AttributeError:
            self.faulty_links.append(url_path)
            return False

    def close(self):
        self.db.close()