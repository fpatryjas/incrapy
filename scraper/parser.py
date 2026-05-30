import re
from bs4 import BeautifulSoup as bs
from scraper.config import selectors

class Parser:
    @staticmethod
    def clean_text(txt):
        return txt.replace("\n", "").replace("\xa0", " ").strip() if txt else ""

    @staticmethod
    def int_from_txt(txt):
        if not txt: return None
        try:
            number = re.findall(r'[0-9]+[,]?[0-9]*', str(txt))[0]
            return int(number.replace(",", ""))
        except IndexError:
            return None

    @staticmethod
    def clean_rank(txt):
        return txt[5:] if txt and len(txt) > 5 else None

    def decipher_meta(self, txt):
        if not txt: return None, None, None
        temp = txt.strip("\n").split("\n\n")
        try:
            date = temp[0][7:] if len(temp) > 0 else None
            n_posts = self.int_from_txt(temp[1]) if len(temp) > 1 else None
            time_online = temp[2][8:] if len(temp) > 2 else None
            return date, n_posts, time_online
        except Exception:
            return None, None, None

    def get_thread_type(self, soup):
        message_blocks = soup.select(selectors["thread_blocks"])
        return 1 if len(message_blocks) < 2 else 0

    def parse_comments(self, soup, title, table_name, thread_id=0, thread_activity=None):
        articles = soup.select(selectors["articles"])
        if not articles: return []

        if thread_id == 0:
            html_tag = soup.find("html")
            if html_tag and html_tag.has_attr("data-content-key"):
                thread_id = self.int_from_txt(html_tag["data-content-key"])

        posts_data = []
        for a in articles:
            try:
                userdetails = a.find("div", class_="message-userDetails")
                userinfo = userdetails.find("span") if userdetails else None
                if not userinfo: continue
                
                user_id = int(userinfo["data-user-id"])
                user_name = userinfo.text
                user_title = userdetails.find("h5", class_="userTitle").text if userdetails.find("h5", class_="userTitle") else ""
                
                try: rank = self.clean_rank(userdetails.find("div")["class"][1])
                except: rank = None
                
                try: n_stars = len(userdetails.find("div").text)
                except: n_stars = None

                try:
                    meta = "".join(a.find("div", class_="message-userExtras").find_all(text=True, recursive=True))
                    date, n_posts, time_online = self.decipher_meta(meta)
                except:
                    date, n_posts, time_online = None, None, None

                datetime_op = a.find("time", class_="u-dt")["datetime"] if a.find("time", class_="u-dt") else None
                n_post = self.int_from_txt(a.find("header", class_="message-attribution").find_all("li")[-1].text)
                message = "".join(a.find("div", class_="bbWrapper").find_all(text=True, recursive=False))
                
                try: quote_host = str([i["data-host"] for i in a.select(selectors["code_block"])])
                except: quote_host = None
                try: quote_url = str([i["data-url"] for i in a.select(selectors["code_block"])])
                except: quote_url = None
                try:
                    quoted_user = str([i["data-quote"] for i in a.select(selectors["blockquote"])])
                    quoted_user_id = str([self.int_from_txt(i["data-attributes"]) for i in a.select(selectors["blockquote"])])
                except:
                    quoted_user, quoted_user_id = None, None

                posts_data.append((
                    title, thread_id, thread_activity, user_id, user_name, user_title, rank, n_stars,
                    date, n_posts, time_online, datetime_op, n_post, message,
                    quote_host, quote_url, quoted_user, quoted_user_id
                ))
            except Exception as e:
                print(f"Error when parsing post: {e}")
                continue
        return posts_data

    def scrape_op(self, soup_block, thread_activity=None):
        try:
            html_tag = soup_block.find_parent("html")
            thread_id = self.int_from_txt(soup_block["data-lb-id"]) if soup_block.has_attr("data-lb-id") else 0
            text_op = str(soup_block.find("div", class_="bbWrapper").find_all(text=True, recursive=False))
            datetime_op = soup_block.find("time", class_="u-dt")["datetime"] if soup_block.find("time", class_="u-dt") else None
            
            userinfo = soup_block.find("aside", class_="message-articleUserInfo")
            username = userinfo.find("span", class_="username").text if userinfo else "Unknown"
            user_id = int(userinfo.find("span", class_="username")["data-user-id"]) if userinfo else 0
            
            try: user_title = userinfo.find("span", class_="userTitle").text
            except: user_title = None
            
            try:
                n_stars = len(userinfo.find("div", class_="message-articleUserBanners").text)
                rank = self.clean_rank(userinfo.find("div", class_="message-articleUserBanners").find("em")["class"][1])
            except:
                n_stars, rank = None, None

            try: quote_host = str([i["data-host"] for i in soup_block.select(selectors["code_block"])])
            except: quote_host = None
            try: quote_url = str([i["data-url"] for i in soup_block.select(selectors["code_block"])])
            except: quote_url = None
            try:
                quoted_user = str([i["data-quote"] for i in soup_block.select(selectors["blockquote"])])
                quoted_user_id = str([self.int_from_txt(i["data-attributes"]) for i in soup_block.select(selectors["blockquote"])])
            except:
                quoted_user, quoted_user_id = None, None

            return [thread_id, thread_activity, user_id, username, user_title, rank, n_stars, None, None, None, datetime_op, 1, text_op, quote_host, quote_url, quoted_user, quoted_user_id]
        except Exception as e:
            print(f"Error while scraping OP thread: {e}")
            return None