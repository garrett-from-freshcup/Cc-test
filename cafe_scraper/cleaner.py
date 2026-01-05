"""
Data cleaning and normalization for cafe menu data.
"""

import re
from typing import List
from .models import MenuItem, DrinkSize, CafeMenu


class MenuCleaner:
    """Cleans and normalizes menu data."""

    SIZE_MAPPINGS = {
        'sm': 'Small',
        'small': 'Small',
        's': 'Small',
        'md': 'Medium',
        'medium': 'Medium',
        'm': 'Medium',
        'reg': 'Regular',
        'regular': 'Regular',
        'lg': 'Large',
        'large': 'Large',
        'l': 'Large',
        'xl': 'Extra Large',
        'extra large': 'Extra Large',
        'x-large': 'Extra Large',
    }

    VOLUME_PATTERNS = {
        r'(\d+)\s*oz': lambda m: f"{m.group(1)}oz",
        r'(\d+)\s*ml': lambda m: f"{m.group(1)}ml",
    }

    def __init__(self):
        self.size_mapping = self.SIZE_MAPPINGS.copy()

    def clean_menu(self, menu: CafeMenu) -> CafeMenu:
        """
        Clean and normalize an entire menu.

        Args:
            menu: The menu to clean

        Returns:
            Cleaned CafeMenu object
        """
        cleaned_items = [self.clean_item(item) for item in menu.items]
        menu.items = cleaned_items
        return menu

    def clean_item(self, item: MenuItem) -> MenuItem:
        """
        Clean and normalize a menu item.

        Args:
            item: The menu item to clean

        Returns:
            Cleaned MenuItem object
        """
        item.name = self._clean_text(item.name)
        item.category = self._normalize_category(item.category)

        if item.description:
            item.description = self._clean_text(item.description)

        item.sizes = [self._clean_size(size) for size in item.sizes]

        item.sizes = self._deduplicate_sizes(item.sizes)

        if item.sizes and item.base_price is None:
            item.base_price = min(size.price for size in item.sizes)

        return item

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        text = text.replace('\u2019', "'")
        text = text.replace('\u2018', "'")
        text = text.replace('\u201c', '"')
        text = text.replace('\u201d', '"')
        text = text.replace('\u2013', '-')
        text = text.replace('\u2014', '-')

        return text

    def _normalize_category(self, category: str) -> str:
        """Normalize category names."""
        category = self._clean_text(category)

        category_mappings = {
            'coffee': 'Coffee',
            'espresso': 'Espresso',
            'tea': 'Tea',
            'latte': 'Coffee',
            'cappuccino': 'Coffee',
            'cold brew': 'Cold Brew',
            'iced coffee': 'Iced Coffee',
            'iced tea': 'Iced Tea',
            'smoothie': 'Smoothies',
            'smoothies': 'Smoothies',
            'food': 'Food',
            'pastry': 'Pastries',
            'pastries': 'Pastries',
            'sandwich': 'Sandwiches',
            'sandwiches': 'Sandwiches',
            'breakfast': 'Breakfast',
            'lunch': 'Lunch',
            'snack': 'Snacks',
            'snacks': 'Snacks',
        }

        category_lower = category.lower()
        for key, value in category_mappings.items():
            if key in category_lower:
                return value

        return category.title()

    def _clean_size(self, size: DrinkSize) -> DrinkSize:
        """Clean and normalize a drink size."""
        size.name = self._normalize_size_name(size.name)

        size.price = round(size.price, 2)

        if size.volume:
            size.volume = self._normalize_volume(size.volume)
        else:
            size.volume = self._extract_volume_from_name(size.name)

        return size

    def _normalize_size_name(self, name: str) -> str:
        """Normalize size names to standard values."""
        name = self._clean_text(name)
        name_lower = name.lower().strip()

        volume = self._extract_volume_from_name(name_lower)
        if volume:
            name_lower = re.sub(r'\d+\s*(oz|ml)', '', name_lower).strip()

        if name_lower in self.size_mapping:
            return self.size_mapping[name_lower]

        for key, value in self.size_mapping.items():
            if key in name_lower:
                return value

        return name.title()

    def _normalize_volume(self, volume: str) -> str:
        """Normalize volume strings."""
        volume = volume.lower().strip()

        for pattern, formatter in self.VOLUME_PATTERNS.items():
            match = re.search(pattern, volume)
            if match:
                return formatter(match)

        return volume

    def _extract_volume_from_name(self, name: str) -> str:
        """Extract volume information from size name."""
        for pattern in self.VOLUME_PATTERNS.keys():
            match = re.search(pattern, name.lower())
            if match:
                return self._normalize_volume(match.group(0))
        return None

    def _deduplicate_sizes(self, sizes: List[DrinkSize]) -> List[DrinkSize]:
        """Remove duplicate sizes, keeping the one with lower price."""
        size_dict = {}

        for size in sizes:
            key = (size.name, size.volume or '')

            if key not in size_dict or size.price < size_dict[key].price:
                size_dict[key] = size

        return list(size_dict.values())

    def merge_menus(self, menus: List[CafeMenu]) -> List[CafeMenu]:
        """
        Merge and deduplicate menus from the same location.

        Args:
            menus: List of CafeMenu objects

        Returns:
            List of merged CafeMenu objects
        """
        location_menus = {}

        for menu in menus:
            key = (menu.location.name, menu.location.address)

            if key not in location_menus:
                location_menus[key] = menu
            else:
                existing = location_menus[key]
                existing.items.extend(menu.items)

                if menu.scraped_at > existing.scraped_at:
                    existing.scraped_at = menu.scraped_at

        for menu in location_menus.values():
            menu.items = self._deduplicate_items(menu.items)

        return list(location_menus.values())

    def _deduplicate_items(self, items: List[MenuItem]) -> List[MenuItem]:
        """Remove duplicate menu items."""
        item_dict = {}

        for item in items:
            key = (item.name.lower(), item.category)

            if key not in item_dict:
                item_dict[key] = item
            else:
                existing = item_dict[key]
                for size in item.sizes:
                    if not any(s.name == size.name for s in existing.sizes):
                        existing.sizes.append(size)

                existing.sizes = self._deduplicate_sizes(existing.sizes)

        return list(item_dict.values())
