from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


@register.filter
def percent(value, total):
    """`value` as a 0-100 share of `total`, one decimal place; 0 when total is 0."""
    total = _to_decimal(total)
    if total <= 0:
        return 0
    share = _to_decimal(value) / total * 100
    return float(round(max(Decimal('0'), min(share, Decimal('100'))), 1))


@register.filter
def with_pct(rows, key):
    """Return rows as dicts with a `pct` entry scaled against the largest `key` value.

    Works on dict rows (values() querysets, lists of dicts). Used to size bars and columns."""
    rows = [dict(row) for row in rows]
    peak = max((_to_decimal(row.get(key)) for row in rows), default=Decimal('0'))
    for row in rows:
        row['pct'] = percent(row.get(key), peak)
    return rows


@register.simple_tag
def bar_pct(value, peak):
    return percent(value, peak)


@register.filter
def money(value):
    """Format an amount as $1,234.50, with the minus sign before the currency symbol."""
    amount = _to_decimal(value).quantize(Decimal('0.01'))
    sign = '-' if amount < 0 else ''
    return f'{sign}${abs(amount):,.2f}'
