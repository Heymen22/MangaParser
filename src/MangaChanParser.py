import asyncio

import aiohttp
from bs4 import BeautifulSoup
from urllib3.util import Url


def get_page_data():
    pass

async def get_pages() -> list[str]:
    url = "https://manga-chan.me/manga/new&n=dateasc"

    async with aiohttp.ClientSession as session:
        response = await session.get(url=url)
        soup = BeautifulSoup(await response.text, "lxml")
        pages = [url + a["href"] for a in soup.find("div", id="pagination").find("span").find_all("a")]
        print(pages)


if __name__ == "__main__":
    asyncio.run(get_pages())