import aiohttp
import asyncio
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from aiohttp_retry import RetryClient, ExponentialRetry
from fake_useragent import UserAgent


load_dotenv()

category_lst = []
pagen_lst = []
domain = os.getenv("DOMAIN")


def get_soup(url):
    resp = requests.get(url=url, verify=False)
    return BeautifulSoup(resp.text, 'lxml')


def get_urls_categories(soup):
    all_link = soup.find('div', class_='nav_menu').find_all('a')

    for cat in all_link:
        category_lst.append(domain + cat['href'])


def get_urls_pages(category_lst):
    # Заносит ссылки на все страницы в категориях в общий список pagen_lst

    for cat in category_lst:
        soup = get_soup(cat)
        for pagen in soup.find('div', class_='pagen').find_all('a'):
            pagen_lst.append(domain + pagen['href'])


async def get_data(session, link):
    retry_options = ExponentialRetry(attempts=5)
    retry_client = RetryClient(
        raise_for_status=False,
        retry_options=retry_options,
        client_session=session,
        start_timeout=0.5)
    async with retry_client.get(link) as response:
        if response.ok:
            resp = await response.text()
            soup = BeautifulSoup(resp, 'lxml')
            item_card = [
                x['href'] for x in soup.find_all('a', class_='name_item')]
            for x in item_card:
                url2 = domain + x
                async with session.get(url=url2) as response2:
                    resp2 = await response2.text()
                    soup2 = BeautifulSoup(resp2, 'lxml')
                    article = soup2.find('p', class_='article').text
                    name = soup2.find('p', id='p_header').text
                    price = soup2.find('span', id='price').text
                    print(url2, price, article, name)


async def main():
    ua = UserAgent()
    fake_ua = {'user-agent': ua.random}
    async with aiohttp.ClientSession(headers=fake_ua) as session:
        tasks = []
        for link in pagen_lst:
            task = asyncio.create_task(get_data(session, link))
            tasks.append(task)
        await asyncio.gather(*tasks)


url = os.getenv("LINK")
soup = get_soup(url)
get_urls_categories(soup)
get_urls_pages(category_lst)

asyncio.run(main())
