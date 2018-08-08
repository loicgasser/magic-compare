# -*- utf-8 -*-

import re
import sys
import requests
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
def mkm_booster_name(url, base_path):
    a, name = url.split(base_path)
    return name.replace("+", " ").replace("/", " ")


def mkm_find_booster_urls(soup):
    for img in find_all_by_class(soup, "gw_ImageBox"):
        yield "{0}{1}".format(MKM_BASE_URL, img.find("a").get("href"))


def mkm_fetch_index_booster_pages(url, from_page, to_page):
    param = "resultsPage="
    for i in range(from_page, to_page):
        yield parse_html_document(fetch_page("{0}?{1}{2}".format(url, param, i)))



# We only want english and boosters in Switzerland for now
def mkm_get_booster_info(soup):
    table_body = find_unique_element_by_id(soup, "articlesTable")
    for row in list(table_body.children):
        # No class on relevant rows
        if not row.get("class"):
            seller_country = row.find(
                attrs={"data-original-title": re.compile("Item location")})
            if not seller_country or "Switzerland" not in seller_country.get("data-original-title"):
                continue
            booster_lang = row.find(attrs={"data-original-title": "English"})
            if not booster_lang:
                continue
            user = row.find(href=re.compile("Users"))
            user = user.string
            sys.exit(0)


def mkm_fetch_boosters_pages(url, from_page, to_page):
    for index_page in mkm_fetch_index_booster_pages(url, from_page, to_page):
        print("Parsing Index Booster Page {}".format(url))
        for booster_url in mkm_find_booster_urls(index_page):
            print("Parsing Booster Page for {}".format(
                mkm_booster_name(booster_url, "{0}{1}".format(
                    MKM_BASE_URL, MKM_BASE_PATH))))
            yield parse_html_document(fetch_page(booster_url))


def main():
    url = "{0}{1}".format(MKM_BASE_URL, MKM_BASE_PATH)
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
    number_of_pages = int(tag.string)
    # No need to add one because indexing starts at 0
    for booster_page in mkm_fetch_boosters_pages(url, 1, number_of_pages):
        mkm_get_booster_info(booster_page)
    return


if __name__ == "__main__":
    main()
