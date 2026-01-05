"""
Data models for cafe menu items.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class DrinkSize:
    """Represents a drink size option."""
    name: str
    price: float
    volume: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MenuItem:
    """Represents a menu item (drink, food, etc.)."""
    name: str
    category: str
    description: Optional[str] = None
    sizes: List[DrinkSize] = field(default_factory=list)
    base_price: Optional[float] = None
    modifiers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['sizes'] = [size.to_dict() for size in self.sizes]
        return data


@dataclass
class CafeLocation:
    """Represents a cafe location."""
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    url: str
    phone: Optional[str] = None
    hours: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CafeMenu:
    """Represents a complete cafe menu."""
    location: CafeLocation
    items: List[MenuItem] = field(default_factory=list)
    scraped_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'location': self.location.to_dict(),
            'items': [item.to_dict() for item in self.items],
            'scraped_at': self.scraped_at.isoformat()
        }

    def get_items_by_category(self, category: str) -> List[MenuItem]:
        """Filter items by category."""
        return [item for item in self.items if item.category.lower() == category.lower()]

    def get_items_by_size(self, size_name: str) -> List[MenuItem]:
        """Filter items that have a specific size option."""
        return [
            item for item in self.items
            if any(size.name.lower() == size_name.lower() for size in item.sizes)
        ]

    def search_items(self, query: str) -> List[MenuItem]:
        """Search items by name or description."""
        query_lower = query.lower()
        return [
            item for item in self.items
            if query_lower in item.name.lower() or
               (item.description and query_lower in item.description.lower())
        ]
