import logging
import logging.config
from itertools import chain
from typing import Any

import requests
import telebot
from bs4 import BeautifulSoup
from dotenv import dotenv_values

URL = 'https://www.asn-news.ru/news'
DOMEN = 'https://www.asn-news.ru/'
CONFIG = dotenv_values()


class BotNewsSender:
    """
    Use Python 3.8
    """

    def __init__(self, url: str):
        self.token = CONFIG.get('TOKEN')
        self.chat_id = CONFIG.get('CHAT_ID')
        self.url = url
        self.bot = telebot.TeleBot(self.token)

    def start(self):
        message = self._get_last_news()
        logger.info("Got news")
        self._send_message_to_telegram_channel(message)
        logger.info("Send news to telegram channel")

    def _send_message_to_telegram_channel(self, message: str):
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def _get_last_news(self):
        page_content = self._get_response_from_url(self.url)
        if page_content:
            last_news_link = self._get_last_news_link(page_content)
            if last_news_link is not None:
                page_content = self._get_response_from_url(last_news_link)
                return self._get_data_text(page_content)
        logger.info("No any news")

    @staticmethod
    def _get_data_text(page_content: str) -> str:
        full_text = []
        title, lead, text = str(), str(), str()
        soup = BeautifulSoup(page_content, 'html.parser')
        for data in soup.find_all(name='h1', attrs={'class': 'main-article__title'}):
            title = f'{data.get_text()}'.strip('\n').split(' ')

        for data in soup.find_all(name='div', attrs={'class': 'main-article__lead'}):
            lead = data.get_text().strip('\n').split(' ')

        for data in soup.find_all(name='div', attrs={'class': 'article-text-editor'}):
            text = data.get_text().strip('\n').split(' ')
        full_text.extend([word for word in chain(title, lead, text) if bool(len(word)) and len(word) < 20
                          and word not in ('{', '}')])
        return ' '.join(full_text)

    @staticmethod
    def _get_last_news_link(page_content: str) -> str:
        soup = BeautifulSoup(page_content, 'html.parser')
        for tag_data in soup.find_all(name='a', attrs={'class': 'default-new__title'}):
            link = tag_data.attrs.get('href', None)
            logger.debug(f'link - {link}')
            if link is not None:
                return f"{DOMEN}{link}"

    @staticmethod
    def _get_response_from_url(url: str) -> Any:
        response = requests.get(url)
        logger.debug(f'response.status_code - {response.status_code}')
        if response.status_code == requests.codes.ok:
            return response.text
        return None


log_config = {
    'version': 1,
    'formatters': {
        'console_formatter': {
            'format': '%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'console_formatter',
        },
    },
    'loggers': {
        'console_logger': {
            'handlers': ['console_handler'],
            'level': 'INFO',
        },
    },
}


logging.config.dictConfig(log_config)
logger = logging.getLogger('console_logger')


if __name__ == '__main__':
    bot = BotNewsSender(url=URL)
    bot.start()
