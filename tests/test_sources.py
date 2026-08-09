import unittest

from fibre_bot.sources import (
    FIXED_NETWORK_TERMS,
    MOBILE_ONLY_TERMS,
    _article_url_is_allowed,
    _clean_markup,
    _validate_feed_url,
)


class SourceTests(unittest.TestCase):
    def test_markup_is_removed(self):
        self.assertEqual(_clean_markup("<p>Full &amp; fibre</p>"), "Full & fibre")

    def test_non_allowlisted_feed_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "allowlist"):
            _validate_feed_url("https://example.com/feed")

    def test_non_https_feed_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "allowlist"):
            _validate_feed_url("http://www.ispreview.co.uk/index.php/feed")

    def test_mobile_only_terms_do_not_overlap_fixed_network_terms(self):
        self.assertTrue(set(MOBILE_ONLY_TERMS).isdisjoint(FIXED_NETWORK_TERMS))

    def test_article_url_must_be_https_and_allowlisted(self):
        self.assertTrue(
            _article_url_is_allowed("https://www.ispreview.co.uk/index.php/example")
        )
        self.assertFalse(_article_url_is_allowed("https://example.com/story"))
        self.assertFalse(
            _article_url_is_allowed("http://www.ispreview.co.uk/index.php/example")
        )


if __name__ == "__main__":
    unittest.main()
