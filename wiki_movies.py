import scrapy
import re
from urllib.parse import unquote
import random

class WikiMoviesSpider(scrapy.Spider):
    name = "wiki_movies"
    allowed_domains = ["ru.wikipedia.org"]
    start_urls = [
        "https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"
    ]

    def parse(self, response):
        links = response.css("div.mw-category a::attr(href)").getall()

        links = [link for link in links if link.startswith("/wiki/") and ":" not in link]

        random_links = random.sample(links, min(30, len(links)))

        for link in random_links:
            yield response.follow(link, callback=self.parse_movie)

        next_page = response.css("a:contains('Следующая страница')::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_movie(self, response):
        title = response.xpath("//h1[@id='firstHeading']/text()").get()
        if not title:
            title = response.url.split("/")[-1]
            title = unquote(title).replace("_", " ")
        title = re.sub(r"\s*\(.*?\)", "", title).strip()

        genre_links = response.xpath("//table[contains(@class,'infobox')]//td//a/text()").getall()
        genre_links = [g.strip() for g in genre_links if g.strip()]
        genre = genre_links[0] if genre_links else "Жанр не найден"

        director_link = response.xpath(
            "//table[contains(@class,'infobox')]//tr[th[contains(translate(text(),'РЕЖИСС','режисс'),'режисс')]]/td//a/text()"
        ).get()
        if not director_link:
            director_link = response.xpath(
                "//table[contains(@class,'infobox')]//tr[th[contains(translate(text(),'РЕЖИСС','режисс'),'режисс')]]/td//text()"
            ).get()
        director = director_link.strip() if director_link else "Нет данных"

        country_td = response.xpath(
            "//table[contains(@class,'infobox')]//tr[th[contains(translate(text(),'СТРАН','стра'),'стра')]]/td//text()"
        ).getall()
        country_list = [re.sub(r"\[\d+\]", "", c).strip() for c in country_td if c.strip()]
        country = country_list[0] if country_list else "Нет данных"

        year_list = response.xpath(
            "//table[contains(@class,'infobox')]//tr[th[contains(translate(text(),'ГОД','год'),'год') or contains(translate(text(),'Дата выхода','дата выхода'),'дата выхода')]]/td//text()"
        ).getall()
        year_list = [y.strip() for y in year_list if y.strip()]
        year_match = re.search(r"\d{4}", " ".join(year_list))
        year = year_match.group(0) if year_match else "Нет данных"

        yield {
            "Название": title,
            "Жанр": genre,
            "Режиссер": director,
            "Страна": country,
            "Год": year,
        }

