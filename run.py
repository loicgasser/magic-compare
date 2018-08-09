# -*- coding: utf-8 -*-

import re
import sys
import requests
from urllib.parse import unquote
from bs4 import BeautifulSoup


MKM_BASE_URL = "https://www.cardmarket.com"
MKM_BASE_PATH = "/en/Magic/Products/Boosters"


def fetch_page(url):
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        return r.content


def parse_html_document(html_doc):
    return BeautifulSoup(html_doc, "html.parser")


def find_unique_element_by_id(soup, el_id):
    return soup.find(id=el_id)


def find_all_by_class(soup, el_class):
    return soup.find_all(class_=el_class)


# MKM specific methods
def mkm_first_index_page(url):
    html_doc = fetch_page(url)
    if not html_doc:
        print("Unable to fetch {} base page".format(url))
        sys.exit(1)
    soup = parse_html_document(html_doc)
    # Paging number
    tag = find_unique_element_by_id(soup, "toResultBottom")
    if not tag or not tag.string.isdigit():
        print("Could not find the number of pages required")
        sys.exit(1)
    to_page = int(tag.string)
    return soup, to_page


def mkm_booster_name(url, base_path):
    name = url.split(base_path)
    return unquote(name[1]).replace("+", " ").replace("/", "")


def mkm_find_booster_urls(soup):
    for img in find_all_by_class(soup, "gw_ImageBox"):
        yield "{0}{1}".format(MKM_BASE_URL, img.find("a").get("href"))


def mkm_fetch_index_booster_pages(url, from_page):
    soup, to_page = mkm_first_index_page(url)
    yield soup
    param = "resultsPage="
    for i in range(from_page + 1, to_page):
        yield parse_html_document(fetch_page("{0}?{1}{2}".format(url, param, i)))


def mkm_is_swiss_seller(row):
    seller_country = row.find(
        attrs={"data-original-title": re.compile("Item location")})
    return not seller_country or "Switzerland" not in seller_country.get("data-original-title")


def mkm_is_english_card(row):
    return not row.find(attrs={"data-original-title": "English"})


def mkm_get_user(row):
    user = row.find(href=re.compile("Users"))
    return user.string


def mkm_get_price(row):
    price = row.find(id=re.compile("price"))
    m = re.match(r"([0-9]*),([0-9]*)", list(price.children)[0].string)
    return float("{0}.{1}".format(m.group(1), m.group(2)))


# We only want english and boosters in Switzerland for now
def mkm_get_booster_info(soup):
    table_body = find_unique_element_by_id(soup, "articlesTable")
    for row in list(table_body.children):
        # No class on relevant rows
        if not row.get("class"):
            if mkm_is_swiss_seller(row):
                continue
            if mkm_is_english_card(row):
                continue
            user = mkm_get_user(row)
            price = mkm_get_price(row)
            return user, price
    return None, None


def mkm_fetch_boosters_pages(url, from_page):
    for index_page in mkm_fetch_index_booster_pages(url, from_page):
        for booster_url in mkm_find_booster_urls(index_page):
            print("Parsing Booster Page for {}".format(
                mkm_booster_name(booster_url, "{0}{1}".format(
                    MKM_BASE_URL, MKM_BASE_PATH))))
            yield booster_url, parse_html_document(fetch_page(booster_url))


def main():
    url = "{0}{1}".format(MKM_BASE_URL, MKM_BASE_PATH)
    for booster_url, booster_soup in mkm_fetch_boosters_pages(url, 0):
        user, price = mkm_get_booster_info(booster_soup)
        if user and price:
            print("User {0} has a booster at {1} Euros to sell".format(user, price))
            print("Visit {} to make a purchase".format(booster_url))
    return


if __name__ == "__main__":
    main()
