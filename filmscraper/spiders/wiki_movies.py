import json
import re
from urllib.parse import urljoin

import scrapy

from filmscraper.items import MovieItem


class WikiMoviesSpider(scrapy.Spider):
    name = "wiki_movies"
    allowed_domains = ["ru.wikipedia.org", "imdb.com", "www.imdb.com"]
    start_urls = [
        "https://ru.wikipedia.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%A4%D0%B8%D0%BB%D1%8C%D0%BC%D1%8B_%D0%BF%D0%BE_%D0%B0%D0%BB%D1%84%D0%B0%D0%B2%D0%B8%D1%82%D1%83",
        "https://ru.wikipedia.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%A4%D0%B8%D0%BB%D1%8C%D0%BC%D1%8B_%D0%BF%D0%BE_%D0%B3%D0%BE%D0%B4%D0%B0%D0%BC",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    }

    def parse(self, response):
        for a in response.css("div#mw-subcategories a"):
            href = a.attrib.get("href", "")
            title_text = "".join(a.css("::text").getall()).strip()
            if "/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:" in href:
                yield response.follow(href, callback=self.parse)

        for a in response.css("div#mw-pages div.mw-category a"):
            href = a.attrib.get("href", "")
            if "/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:" in href:
                continue
            if href.startswith("/wiki/"):
                yield response.follow(href, callback=self.parse_movie)

        for a in response.css("div#mw-pages a"):
            text = "".join(a.css("::text").getall()).strip()
            if "Следующая страница" in text:
                yield response.follow(a.attrib.get("href", ""), callback=self.parse)

    def parse_movie(self, response):
        item = MovieItem()
        item["url"] = response.url

        title = response.css("h1#firstHeading::text").get()
        if title:
            item["title"] = title.strip()
        info_rows = response.css("table.infobox tr")

        def extract_cell_text(td_sel):
            texts = td_sel.xpath(".//text()").getall()
            texts = [t.strip() for t in texts if t.strip()]
            return ", ".join(dict.fromkeys(texts)) if texts else None

        header_map = {
            "Жанр": "genre",
            "Режиссёр": "director",
            "Режиссер": "director",
            "Страна": "country",
            "Год": "year",
            "Год выпуска": "year",
            "Годы": "year",
        }

        for row in info_rows:
            header = row.css("th::text").get()
            if not header:
                continue
            header = header.strip()
            target_field = header_map.get(header)
            if not target_field:
                continue
            value = extract_cell_text(row.css("td"))
            if not value:
                continue
            if target_field == "year":
                m = re.search(r"(19|20)\d{2}", value)
                item["year"] = m.group(0) if m else value
            else:
                item[target_field] = value

        imdb_href = response.css('a[href*="imdb.com/title/tt"]::attr(href)').get()
        if imdb_href:
            imdb_url = imdb_href
            if imdb_url.startswith("//"):
                imdb_url = "https:" + imdb_url
            elif imdb_url.startswith("/"):
                imdb_url = urljoin("https://www.imdb.com", imdb_url)
            item["imdb_url"] = imdb_url
            yield scrapy.Request(
                imdb_url,
                callback=self.parse_imdb,
                meta={"item": item},
                headers={"Referer": response.url},
            )
        else:
            yield item

    def parse_imdb(self, response):
        item = response.meta["item"]

        rating_value = None

        json_ld_list = response.css('script[type="application/ld+json"]::text').getall()
        for blob in json_ld_list:
            try:
                data = json.loads(blob)
            except Exception:
                continue
            if isinstance(data, list):
                candidates = data
            else:
                candidates = [data]
            for d in candidates:
                agg = d.get("aggregateRating") if isinstance(d, dict) else None
                if isinstance(agg, dict):
                    val = agg.get("ratingValue")
                    if val:
                        rating_value = str(val).strip()
                        break
            if rating_value:
                break

        if not rating_value:
            txt = response.css(
                '[data-testid="hero-rating-bar__aggregate-rating__score"] span::text'
            ).get()
            if txt:
                rating_value = txt.strip()

        item["imdb_rating"] = rating_value
        yield item

