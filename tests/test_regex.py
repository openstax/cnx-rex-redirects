import unittest
import re
from rex_redirects import cnx_uri_regex

class TestUriRegex(unittest.TestCase):
    def setUp(self):
        self.book = {
            "id": "book-long-id",
            "short_id": "bookshortid"
        }
        self.page = {
            "id": "page-long-id",
            "short_id": "pageshortid"
        }
        self.base_uri = "/contents/bookshortid:pageshortid/slug"

    def test_no_query_string_redirect(self):
        """Baseline test to ensure redirects match as expected when no query
        parameters are present
        """
        regex = cnx_uri_regex(self.book, self.page)
        map_redirect = re.compile(regex)

        self.assertRegex(f"{self.base_uri}", map_redirect)

    def test_android_no_redirect(self):
        """All requests for REX books that come from the Android App
        should continue to pass through to the cnx site (these requests
        are indicated by the attachment of the query-string: `?minimal=true`)
        https://github.com/openstax/cnx/issues/343
        """
        regex = cnx_uri_regex(self.book, self.page)
        map_redirect = re.compile(regex)

        self.assertNotRegex(f"{self.base_uri}?minimal=true", map_redirect)
        self.assertNotRegex(
            f"{self.base_uri}?utm_campaign=Campaign&minimal=true&utm_source=Source",
            map_redirect
        )
        self.assertNotRegex(
            f"{self.base_uri}?utm_campaign=Campaign&utm_source=Source&minimal=true",
            map_redirect
        )

    def test_query_string_redirect(self):
        """Requests with query parameters should still redirect
        https://github.com/openstax/cnx/issues/921
        """
        regex = cnx_uri_regex(self.book, self.page)
        map_redirect = re.compile(regex)

        query_params = "utm_source=Source&utm_medium=Medium&utm_campaign=Campaign"
        self.assertRegex(f"{self.base_uri}?{query_params}", map_redirect)
