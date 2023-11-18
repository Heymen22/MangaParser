import json
import logging
import multiprocessing
from typing import Iterable, NamedTuple

import requests
from bs4 import BeautifulSoup
from urllib3.util import parse_url

from src.MangaTypes import Manga, Status


def get_soup_object(parsing_url: str):
    response = requests.get(parsing_url)
    return BeautifulSoup(markup=response.text, features="html.parser")


def _parse_manga_page(manga_page_url: str) -> Manga:
    soup = get_soup_object(manga_page_url)
    # noinspection SpellCheckingInspection
    title_table_body = soup.find("table", class_="mangatitle")
    title = soup.find("a", class_="title_top_a").string
    author = title_table_body.find("td", class_="item", string="Автор").findNext("td", class_="item2").span.a.string
    status_volume_field = title_table_body.find("td", class_="item", string="Статус (Томов)").findNext(
        "td", class_="item2").string
    if status_volume_field == 'Сингл':
        volumes = 1
        manga_status = Status.COMPLETED
    else:
        volume_str, manga_status_str = status_volume_field.split(', ')
        volumes = int(volume_str.split(' ')[0])
        match manga_status_str:
            case "выпуск продолжается":
                manga_status = Status.CONTINUES
            case _:
                manga_status = Status.UNDEFINED
                logging.info("Нераспознанный статус манги", manga_status_str)
    # noinspection SpellCheckingInspection
    tags = [tag_link.string for tag_link in
            title_table_body.find("td", class_="item", string="Тэги").findNext("td", class_="item2").find_all("a")]
    translators = [translator_link.string for translator_link in
                   title_table_body.find("td", class_="item", string="Переводчики").
                   findNext("td", class_="item2").find_all("a")]
    chapter_str, translate_status_str = title_table_body.find("td", class_="item", string="Загружено").findNext(
        "td",
        class_="item2").text.split(
        ", ")
    chapters = int(chapter_str.split(' ')[0])

    match translate_status_str:
        case "перевод продолжается":
            translate_status = Status.CONTINUES
        case "перевод завершен":
            translate_status = Status.COMPLETED
        case _:
            translate_status = Status.UNDEFINED
            logging.info("Нераспознанный статус манги", translate_status_str)
    manga = Manga(
        url=manga_page_url,
        title=title,
        author=author,
        manga_status=manga_status,
        chapters=chapters,
        volumes=volumes,
        translators=translators,
        translate_status=translate_status,
        tags=tags
    )
    print(manga)
    return manga


def _get_manga_links_on_page(page_url: str):
    parsed_url = parse_url(page_url)
    soup = get_soup_object(page_url)
    manga_links = soup.find_all("a", class_="title_link")
    if len(manga_links) <= 0:
        raise StopIteration
    for title in soup.find_all("a", class_="title_link"):
        yield f"{parsed_url.scheme}://{parsed_url.netloc}{title['href']}"


def _get_manga_url(catalog_url: str) -> Iterable[str]:
    offset = 0
    parsed_url = parse_url(catalog_url)
    while True:
        offset += 20
        page_url = f"{catalog_url}?{offset=}"
        soup = get_soup_object(page_url)
        manga_links = soup.find_all("a", class_="title_link")
        if len(manga_links) <= 0:
            break
        # if offset == 100:
        #     break
        for title in soup.find_all("a", class_="title_link"):
            yield f"{parsed_url.scheme}://{parsed_url.netloc}{title['href']}"


# def _get_next_manga_url(catalog_url: str) -> Iterable[str]:
#     for page_link in _get_pages_urls(catalog_url):
#         for manga_link_list in _get_manga_links_on_page(page_link):
#             yield manga_link_list


class MangaChanParser:

    def __init__(self):
        self.URL: str = "https://manga-chan.me/manga/new"
        self.pages_url: list[str] = []

    # def run(self):
    #     self.pages_url = self._get_page_urls()

    # def _get_manga_urls_from_page(self, page: Tag):
    #     pass
    # def _get_manga_urls(self, page_url: str):
    #     soup = get_soup_object(page_url)
    #     return [manga_url for manga_url in soup.find_all(name="a", class_="title_link")]

    # def _parse_page(self, page_url: str):
    #     response = requests.get(page_url)
    #     html = response.text
    #     soup = BeautifulSoup(markup=html, features="html.parser")
    #     manga_div_list = soup.find_all(name="div", class_="content_row")
    #     return manga_div_list


class MangaException(NamedTuple):

    url: str
    e: Exception


def get_manga_from_url(manga_url: str, bad_manga):
    try:
        _parse_manga_page(manga_page_url=manga_url)
    except Exception as e:
        # logger = logging.Logger(name="manga-logger")
        # logger.basicConfig(filename=f"logs/{manga_url}/manga.log", encoding="UTF-8", level=logging.DEBUG)
        bad_manga.put(MangaException(manga_url, e))


if __name__ == "__main__":

    proccess = []
    bad_manga = multiprocessing.Queue()
    Errors = []

    for manga_url in _get_manga_url("https://manga-chan.me/manga/new"):
        # _parse_manga_page(manga_page_url=manga_url)
        proc = multiprocessing.Process(target=get_manga_from_url, args=(manga_url, bad_manga))
        proccess.append(proc)
        proc.start()

    while True:
        for procces in proccess:
            if procces.is_alive():
                break
        else:
            for shit in iter(bad_manga.get, None):
                Errors.append(shit)
            with open("logs/bad_manga.log", "w") as f:
                json.dump(Errors, fp=f)
            break
