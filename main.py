# -*- coding: utf-8 -*-
from re import compile
from typing import Any, Generator, Optional

from bs4 import BeautifulSoup, PageElement, Tag
from colorama import Fore
from fake_useragent import UserAgent
from requests import Response, Session
from tqdm import tqdm


class Website:
    user_agent = UserAgent()

    def __init__(self, url: str, *, cookies: dict = None, params: dict = None, headers: dict = None) -> None:
        self.url: str = url
        self.cookies: dict = cookies or {}
        self.params: dict = params or {}
        self.headers: dict = headers or {}

        self.__markup = self.__spider = None

    @property
    def markup(self) -> str:
        if not self.__markup:
            with Session() as session:
                session.headers['User-Agent'] = self.user_agent.random
                session.headers.update(self.headers)

                response: Response = session.get(url=self.url, params=self.params, cookies=self.cookies)
                markup: str = response.text

            self.__markup = markup

        return self.__markup

    @property
    def spider(self) -> BeautifulSoup:
        if not self.__spider:
            self.__spider: BeautifulSoup = BeautifulSoup(markup=self.markup, features='lxml')

        return self.__spider


class Page:
    def __init__(self, *, website: Website) -> None:
        self.spider: BeautifulSoup = website.spider

    @property
    def indexes(self) -> range:
        navigation = self.spider.find(name='div', class_='PageNav')

        if navigation:
            page_counter = navigation.find_all(name='a')[~0]
        else:
            return range(1, 2)

        return range(1, int(page_counter.text) + 1)

    @property
    def page_threads(self) -> Generator[PageElement, Any, None]:
        threads: Optional[Tag] = self.spider.find(name='div', class_='stickyThreads')

        if not threads:
            threads: Tag = self.spider.find(name='div', class_='latestThreads _insertLoadedContent')

        yield from (thread for thread in threads.find_all_next(name='div', id=compile(pattern=r'thread-[0-9]*')))

    @property
    def threads_quantity(self):
        return len([*self.page_threads])


class FileManager:
    @staticmethod
    def load_token(path: str) -> str:
        with open(file=path) as file:
            token: str = file.readline()

        return token


class Scrapper:
    category_id = 663

    prefixes = {
        'Новичок': 464,
        'Любитель': 217,
        'Художник': 404,
        'Полупрофи': 216,
        'Профи': 215,
        'Студия': 496
    }

    @classmethod
    def main(cls):
        url = f'https://zelenka.guru/forums/{cls.category_id}'

        token = FileManager.load_token(path='bin/authorisation/auth_token.txt')

        for name, identifier in cls.prefixes.items():
            params = {'state': 'active', 'prefix_id[]': identifier}

            website = Website(url=url, cookies={'dfuid': token}, params=params)
            indexes = Page(website=website).indexes

            counter = 0

            for index in (progressbar := tqdm(iterable=indexes, desc=f'{name} — 0', unit='pages')):
                website = Website(url=f'{url}/page-{index}', cookies={'dfuid': token}, params=params)
                page = Page(website=website)
                quantity = page.threads_quantity

                counter += quantity
                progressbar.set_description(desc=f'{name} — {counter}')

        input(rf'{Fore.LIGHTMAGENTA_EX}zelenka.guru/members/7558590')


if __name__ == '__main__':
    Scrapper.main()
