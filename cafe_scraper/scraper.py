"""
Web scraper for Square ordering websites.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any
import re
import json
from .models import CafeMenu, CafeLocation, MenuItem, DrinkSize


class SquareScraper:
    """Scraper for Square online ordering websites."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_menu(self, url: str) -> Optional[CafeMenu]:
        """
        Scrape a cafe menu from a Square ordering website.

        Args:
            url: The URL of the Square ordering website

        Returns:
            CafeMenu object if successful, None otherwise
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            location = self._extract_location(soup, url)
            items = self._extract_menu_items(soup)

            return CafeMenu(location=location, items=items)

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def _extract_location(self, soup: BeautifulSoup, url: str) -> CafeLocation:
        """Extract cafe location information from the page."""
        cafe_name = self._find_cafe_name(soup)
        address_info = self._find_address(soup)

        return CafeLocation(
            name=cafe_name or "Unknown Cafe",
            address=address_info.get('address', ''),
            city=address_info.get('city', ''),
            state=address_info.get('state', ''),
            zip_code=address_info.get('zip', ''),
            url=url,
            phone=self._find_phone(soup),
            hours=self._find_hours(soup)
        )

    def _find_cafe_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Find the cafe name from various possible locations."""
        candidates = [
            soup.find('h1'),
            soup.find('title'),
            soup.find(class_=re.compile(r'restaurant.*name|cafe.*name', re.I)),
            soup.find(attrs={'data-testid': re.compile(r'.*name.*', re.I)})
        ]

        for candidate in candidates:
            if candidate and candidate.get_text(strip=True):
                text = candidate.get_text(strip=True)
                text = re.sub(r'\s*-\s*Order.*$', '', text, flags=re.I)
                return text

        return None

    def _find_address(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract address information."""
        address_data = {
            'address': '',
            'city': '',
            'state': '',
            'zip': ''
        }

        address_elem = soup.find(class_=re.compile(r'address', re.I))
        if address_elem:
            text = address_elem.get_text(strip=True)
            parts = [p.strip() for p in text.split(',')]

            if len(parts) >= 3:
                address_data['address'] = parts[0]
                address_data['city'] = parts[1]

                state_zip = parts[2].split()
                if len(state_zip) >= 2:
                    address_data['state'] = state_zip[0]
                    address_data['zip'] = state_zip[1]

        return address_data

    def _find_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Find phone number."""
        phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

        phone_elem = soup.find('a', href=re.compile(r'^tel:'))
        if phone_elem:
            return phone_elem.get_text(strip=True)

        text = soup.get_text()
        match = phone_pattern.search(text)
        return match.group(0) if match else None

    def _find_hours(self, soup: BeautifulSoup) -> Optional[str]:
        """Find operating hours."""
        hours_elem = soup.find(class_=re.compile(r'hours|schedule', re.I))
        if hours_elem:
            return hours_elem.get_text(strip=True)
        return None

    def _extract_menu_items(self, soup: BeautifulSoup) -> List[MenuItem]:
        """Extract menu items from the page."""
        items = []

        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Menu':
                    items.extend(self._parse_structured_menu(data))
            except (json.JSONDecodeError, AttributeError):
                pass

        if not items:
            items = self._parse_html_menu(soup)

        return items

    def _parse_structured_menu(self, data: Dict[str, Any]) -> List[MenuItem]:
        """Parse menu from structured data (JSON-LD)."""
        items = []

        sections = data.get('hasMenuSection', [])
        if not isinstance(sections, list):
            sections = [sections]

        for section in sections:
            category = section.get('name', 'Other')
            menu_items = section.get('hasMenuItem', [])

            if not isinstance(menu_items, list):
                menu_items = [menu_items]

            for item_data in menu_items:
                item = self._parse_menu_item(item_data, category)
                if item:
                    items.append(item)

        return items

    def _parse_menu_item(self, data: Dict[str, Any], category: str) -> Optional[MenuItem]:
        """Parse a single menu item from structured data."""
        name = data.get('name')
        if not name:
            return None

        description = data.get('description', '')

        offers = data.get('offers', [])
        if not isinstance(offers, list):
            offers = [offers]

        sizes = []
        base_price = None

        for offer in offers:
            price = offer.get('price')
            if price:
                try:
                    price_float = float(price)
                    size_name = offer.get('name', 'Regular')

                    sizes.append(DrinkSize(
                        name=size_name,
                        price=price_float
                    ))

                    if base_price is None:
                        base_price = price_float
                except ValueError:
                    pass

        return MenuItem(
            name=name,
            category=category,
            description=description,
            sizes=sizes,
            base_price=base_price
        )

    def _parse_html_menu(self, soup: BeautifulSoup) -> List[MenuItem]:
        """Parse menu items from HTML when structured data is not available."""
        items = []

        menu_sections = soup.find_all(class_=re.compile(r'menu.*section|category', re.I))

        for section in menu_sections:
            category_elem = section.find(re.compile(r'^h[2-4]$'))
            category = category_elem.get_text(strip=True) if category_elem else 'Other'

            item_elements = section.find_all(class_=re.compile(r'menu.*item|product', re.I))

            for item_elem in item_elements:
                name_elem = item_elem.find(class_=re.compile(r'name|title', re.I))
                if not name_elem:
                    continue

                name = name_elem.get_text(strip=True)

                desc_elem = item_elem.find(class_=re.compile(r'description|desc', re.I))
                description = desc_elem.get_text(strip=True) if desc_elem else None

                price_elems = item_elem.find_all(class_=re.compile(r'price', re.I))
                sizes = self._extract_sizes_from_html(price_elems)

                base_price = sizes[0].price if sizes else None

                items.append(MenuItem(
                    name=name,
                    category=category,
                    description=description,
                    sizes=sizes,
                    base_price=base_price
                ))

        return items

    def _extract_sizes_from_html(self, price_elements: List) -> List[DrinkSize]:
        """Extract drink sizes and prices from HTML elements."""
        sizes = []
        price_pattern = re.compile(r'\$?(\d+\.?\d*)')

        for elem in price_elements:
            text = elem.get_text(strip=True)
            match = price_pattern.search(text)

            if match:
                try:
                    price = float(match.group(1))
                    size_name = 'Regular'

                    size_elem = elem.find_previous(class_=re.compile(r'size', re.I))
                    if size_elem:
                        size_name = size_elem.get_text(strip=True)

                    sizes.append(DrinkSize(name=size_name, price=price))
                except ValueError:
                    pass

        if not sizes and price_elements:
            for elem in price_elements:
                text = elem.get_text(strip=True)
                match = price_pattern.search(text)
                if match:
                    try:
                        sizes.append(DrinkSize(
                            name='Regular',
                            price=float(match.group(1))
                        ))
                        break
                    except ValueError:
                        pass

        return sizes
