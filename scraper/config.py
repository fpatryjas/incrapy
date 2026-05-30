import os

thisdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
database = os.path.join(thisdir, "data", "forum.db")

forum = "https://incels.is"

agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
min_d = 0.2
max_d = 0.4
timeout = 60

selectors = {
    "thread_blocks": "div.block--messages",
    "articles": "article.message",
    "user_info": "span[data-user-id]",
    "user_title": "h5.userTitle",
    "user_extras": "div.message-userExtras",
    "datetime": "time.u-dt",
    "attribution": "header.message-attribution",
    "message_wrapper": "div.bbWrapper",
    "code_block": "div.bbCodeBlock",
    "blockquote": "blockquote",
    "title": "div.p-title"
}