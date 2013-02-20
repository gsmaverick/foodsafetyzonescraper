from operator import attrgetter
from bs4 import BeautifulSoup
import requests, re

BASE_SEARCH_URL = "http://www.foodsafetyzone.ca/zonesearch3.asp"

class Search():
    """
        Provides an abstracted interface to making search requests and returns
        results in a sane way.

        :param logger: An instance of a logger to report any errors/warnings.
    """
    def __init__(self, logger):
        self.logger = logger

        self.discover_max_page()

    def discover_max_page(self):
        """
            Finds the number of pages currently available in the system.
        """
        r = requests.get(BASE_SEARCH_URL)
        search_page = BeautifulSoup(r.text)

        # Find all links to a specific page on the results page.
        pages = search_page.find_all("a", attrs={"title": re.compile("Page:")})

        # Find the element that contains the maximum page number.
        max_page = max(pages, key=lambda(x): int(x.contents[0]))

        self.num_pages = int(max_page.contents[0])


    def get_page(self, page):
        """
            Returns a list of the premise IDs on the requested page.

            :param page: Search page to retrieve locations for.
        """
        locations = []
        r = requests.post(BASE_SEARCH_URL, data={'X': page})
        search_results = BeautifulSoup(r.text)
        ids = search_results.find_all("input", attrs={"name": "PremiseID"})

        return [id['value'].strip("'") for id in ids]