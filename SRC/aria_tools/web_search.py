import os
from parallel import Parallel
from dotenv import load_dotenv

load_dotenv("SRC/api_keys.env")
client = Parallel(api_key=os.environ["PARALLEL_API_KEY"])

def search_web(objective, queries):
    search = client.search(
        objective=objective,
        search_queries=queries,
        mode="fast",
    )
    text = ""
    for result in search.results[:5]:
        text += f"Title: {result.title}\nURL: {result.url}\n"
        for excerpt in result.excerpts[:2]:
            text += excerpt[:300]
        text += "\n"
    return text