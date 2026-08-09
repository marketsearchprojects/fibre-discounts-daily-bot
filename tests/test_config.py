import os
import unittest
from unittest.mock import patch

from fibre_bot.config import Settings


class SettingsTests(unittest.TestCase):
    def test_approval_is_false_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(Settings.from_env().approval_granted)

    def test_scope_override_is_rejected(self):
        with patch.dict(os.environ, {"REDDIT_SUBREDDIT": "somewhereElse"}, clear=True):
            with self.assertRaisesRegex(ValueError, "approved only"):
                Settings.from_env()

    def test_only_exact_true_enables_approval(self):
        with patch.dict(os.environ, {"REDDIT_APPROVAL_GRANTED": "TRUE"}, clear=True):
            self.assertFalse(Settings.from_env().approval_granted)
        with patch.dict(os.environ, {"REDDIT_APPROVAL_GRANTED": "true"}, clear=True):
            self.assertTrue(Settings.from_env().approval_granted)


if __name__ == "__main__":
    unittest.main()

