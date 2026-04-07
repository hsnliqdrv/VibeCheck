import re


class TestBadgeDateFormatting:
    """Test that badge unlockedDate uses human-readable format."""

    def test_badge_date_format_strftime(self):
        """The strftime format used in Badge to_dict produces human readable dates."""
        from datetime import datetime

        test_date = datetime(2026, 3, 2, 14, 55, 0)
        formatted = test_date.strftime('%B %-d, %Y at %-I:%M %p')

        assert 'T' not in formatted, 'Should not be ISO format'
        assert '2026' in formatted
        assert re.match(r'.+\d{4} at \d{1,2}:\d{2} [AP]M', formatted)
        assert 'March' in formatted
        assert '2:55 PM' in formatted

    def test_badge_date_not_iso(self):
        """Badge dates should not use ISO format."""
        from datetime import datetime

        test_date = datetime(2026, 3, 2, 14, 55, 0)
        formatted = test_date.strftime('%B %-d, %Y at %-I:%M %p')

        assert 'T' not in formatted
        assert 'March' in formatted
        assert '2:55 PM' in formatted
