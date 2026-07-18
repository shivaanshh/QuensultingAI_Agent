"""Lookup table from a tenant's `category` column to its CategoryTemplate."""
from __future__ import annotations

from .base import CategoryTemplate
from .dental_medical import TEMPLATE as DENTAL_MEDICAL
from .home_services import TEMPLATE as HOME_SERVICES
from .restaurant import TEMPLATE as RESTAURANT
from .salon_spa import TEMPLATE as SALON_SPA

CATEGORY_TEMPLATES: dict[str, CategoryTemplate] = {
    DENTAL_MEDICAL.key: DENTAL_MEDICAL,
    SALON_SPA.key: SALON_SPA,
    RESTAURANT.key: RESTAURANT,
    HOME_SERVICES.key: HOME_SERVICES,
}


def get_template(category: str) -> CategoryTemplate:
    try:
        return CATEGORY_TEMPLATES[category]
    except KeyError:
        raise ValueError(
            f"Unknown category {category!r}. Available: {sorted(CATEGORY_TEMPLATES)}"
        ) from None
