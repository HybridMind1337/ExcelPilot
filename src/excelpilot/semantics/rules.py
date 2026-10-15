"""Heuristic patterns and keyword dictionaries for semantic inference."""

import re
from typing import Final

EMAIL_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

URL_REGEX: Final[re.Pattern[str]] = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

PHONE_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}$"
)

DATE_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})"
)

CURRENCY_SYMBOLS: Final[set[str]] = {"£", "$", "€", "¥", "₹", "chf", "sek"}

CURRENCY_KEYWORDS: Final[set[str]] = {
    "revenue",
    "sales",
    "cost",
    "profit",
    "price",
    "amount",
    "total",
    "fee",
    "charge",
    "salary",
    "expense",
    "budget",
    "billing",
    "subtotal",
    "gross",
    "net",
    "discount",
    "tax",
    "vat",
}

PERCENTAGE_KEYWORDS: Final[set[str]] = {
    "margin",
    "rate",
    "percent",
    "percentage",
    "ratio",
    "pct",
    "share",
    "discount_rate",
    "tax_rate",
    "growth",
}

IDENTIFIER_KEYWORDS: Final[set[str]] = {
    "id",
    "identifier",
    "code",
    "sku",
    "key",
    "number",
    "no",
    "num",
    "guid",
    "uuid",
    "order_id",
    "customer_id",
    "product_id",
    "ref",
    "reference",
}

GEO_KEYWORDS: Final[set[str]] = {
    "country",
    "city",
    "state",
    "province",
    "postal",
    "zip",
    "zipcode",
    "postcode",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "territory",
    "county",
}

TEMPORAL_KEYWORDS: Final[set[str]] = {
    "date",
    "time",
    "datetime",
    "timestamp",
    "year",
    "month",
    "day",
    "period",
    "quarter",
    "created_at",
    "updated_at",
    "order_date",
    "ship_date",
}

BOOLEAN_KEYWORDS: Final[set[str]] = {
    "is_",
    "has_",
    "flag",
    "active",
    "enabled",
    "valid",
    "completed",
    "archived",
}
