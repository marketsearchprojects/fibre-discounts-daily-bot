import unittest
from datetime import UTC, datetime

from fibre_bot.models import Candidate, GeneratedDraft
from fibre_bot.policy import validate_and_compose


SOURCE = Candidate(
    title="Example UK fibre rollout expands",
    url="https://www.ispreview.co.uk/example",
    summary="Example summary",
    published_at=datetime(2026, 8, 9, tzinfo=UTC),
    feed_url="https://www.ispreview.co.uk/index.php/feed",
)


class PolicyTests(unittest.TestCase):
    def test_valid_post_has_two_paragraphs_and_disclosure(self):
        draft = GeneratedDraft(
            title="Example UK fibre rollout reaches more premises",
            flair="UK Fibre News",
            news_paragraph=(
                "A newly announced fibre rollout will extend full-fibre coverage "
                "to additional UK premises. The change matters because households "
                "in the named area may gain access to faster upload and download "
                "options, subject to address-level availability and each provider's "
                "published service terms."
            ),
        )
        post = validate_and_compose(draft, SOURCE)
        self.assertTrue(post.title.startswith("Ad | "))
        self.assertEqual(len(post.body.split("\n\n")), 2)
        self.assertIn("KFJY3B", post.body)
        self.assertIn("I may also receive a referral reward", post.body)
        self.assertIn(SOURCE.url, post.body)

    def test_always_superior_is_blocked(self):
        draft = GeneratedDraft(
            title="Why YouFibre is always superior today",
            flair="Market Development",
            news_paragraph=(
                "This deliberately long example paragraph contains enough words "
                "for validation while attempting a prohibited absolute comparison. "
                "It says a provider is always superior without evidence, which the "
                "publication policy must detect and reject before any submission is made."
            ),
        )
        with self.assertRaisesRegex(ValueError, "Blocked advertising claim"):
            validate_and_compose(draft, SOURCE)

    def test_reward_amount_is_blocked(self):
        draft = GeneratedDraft(
            title="Current switching news with a £100 promise",
            flair="Market Development",
            news_paragraph=(
                "This deliberately long example paragraph contains enough words "
                "for validation while attempting to include a numerical reward. "
                "Time-sensitive offer amounts cannot be generated from an industry "
                "news feed and therefore must be rejected before publication occurs."
            ),
        )
        with self.assertRaisesRegex(ValueError, "Blocked advertising claim"):
            validate_and_compose(draft, SOURCE)


if __name__ == "__main__":
    unittest.main()
