from decimal import Decimal

from django.test import SimpleTestCase

from core.templatetags.ui import money, percent, with_pct


class UiFilterTests(SimpleTestCase):
    def test_money_formats_two_decimals_and_thousands(self):
        self.assertEqual(money(Decimal('316.5')), '$316.50')
        self.assertEqual(money(Decimal('1234567')), '$1,234,567.00')
        self.assertEqual(money(None), '$0.00')

    def test_money_puts_minus_before_symbol(self):
        self.assertEqual(money(Decimal('-49.5')), '-$49.50')

    def test_percent_handles_zero_total_and_clamps(self):
        self.assertEqual(percent(Decimal('5'), Decimal('0')), 0)
        self.assertEqual(percent(Decimal('25'), Decimal('100')), 25.0)
        self.assertEqual(percent(Decimal('150'), Decimal('100')), 100.0)

    def test_with_pct_scales_against_peak(self):
        rows = [{'total': Decimal('10')}, {'total': Decimal('5')}, {'total': Decimal('0')}]
        self.assertEqual([r['pct'] for r in with_pct(rows, 'total')], [100.0, 50.0, 0])

    def test_with_pct_empty(self):
        self.assertEqual(with_pct([], 'total'), [])
