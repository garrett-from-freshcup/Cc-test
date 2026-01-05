"""
Search and filter functionality for cafe menu data.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .models import MenuItem, CafeMenu
from .storage import MenuDatabase


@dataclass
class SearchFilters:
    """Filters for searching menu items."""
    query: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    location_name: Optional[str] = None


class MenuSearcher:
    """Advanced search and filter functionality for menu data."""

    def __init__(self, db_path: str = 'cafe_menus.db'):
        self.db = MenuDatabase(db_path)

    def search(self, filters: SearchFilters) -> List[Dict[str, Any]]:
        """
        Search menu items with various filters.

        Args:
            filters: SearchFilters object with search criteria

        Returns:
            List of dictionaries containing item and location info
        """
        query_parts = []
        params = []

        query = '''
            SELECT
                mi.id,
                mi.name,
                mi.category,
                mi.description,
                mi.base_price,
                l.name as location_name,
                l.city,
                l.state,
                l.address,
                GROUP_CONCAT(ds.name || ':' || ds.price || ':' || IFNULL(ds.volume, ''), '|') as sizes
            FROM menu_items mi
            JOIN locations l ON mi.location_id = l.id
            LEFT JOIN drink_sizes ds ON mi.id = ds.item_id
        '''

        if filters.query:
            query_parts.append('(mi.name LIKE ? OR mi.description LIKE ?)')
            search_term = f'%{filters.query}%'
            params.extend([search_term, search_term])

        if filters.category:
            query_parts.append('mi.category LIKE ?')
            params.append(f'%{filters.category}%')

        if filters.city:
            query_parts.append('l.city LIKE ?')
            params.append(f'%{filters.city}%')

        if filters.state:
            query_parts.append('l.state = ?')
            params.append(filters.state.upper())

        if filters.location_name:
            query_parts.append('l.name LIKE ?')
            params.append(f'%{filters.location_name}%')

        if filters.min_price is not None:
            query_parts.append('mi.base_price >= ?')
            params.append(filters.min_price)

        if filters.max_price is not None:
            query_parts.append('mi.base_price <= ?')
            params.append(filters.max_price)

        if query_parts:
            query += ' WHERE ' + ' AND '.join(query_parts)

        query += ' GROUP BY mi.id ORDER BY l.name, mi.category, mi.name'

        cursor = self.db.conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            sizes_str = row['sizes']
            sizes = []

            if sizes_str:
                for size_str in sizes_str.split('|'):
                    parts = size_str.split(':')
                    if len(parts) >= 2:
                        sizes.append({
                            'name': parts[0],
                            'price': float(parts[1]),
                            'volume': parts[2] if len(parts) > 2 and parts[2] else None
                        })

            if filters.size:
                if not any(
                    filters.size.lower() in size['name'].lower()
                    for size in sizes
                ):
                    continue

            results.append({
                'id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'description': row['description'],
                'base_price': row['base_price'],
                'sizes': sizes,
                'location': {
                    'name': row['location_name'],
                    'city': row['city'],
                    'state': row['state'],
                    'address': row['address']
                }
            })

        return results

    def search_by_text(self, query: str) -> List[Dict[str, Any]]:
        """Simple text search across item names and descriptions."""
        return self.search(SearchFilters(query=query))

    def get_items_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all items in a specific category."""
        return self.search(SearchFilters(category=category))

    def get_items_by_size(self, size: str) -> List[Dict[str, Any]]:
        """Get all items that have a specific size option."""
        return self.search(SearchFilters(size=size))

    def get_items_by_location(self, city: Optional[str] = None,
                             state: Optional[str] = None,
                             location_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get items filtered by location."""
        return self.search(SearchFilters(
            city=city,
            state=state,
            location_name=location_name
        ))

    def get_items_in_price_range(self, min_price: float,
                                 max_price: float) -> List[Dict[str, Any]]:
        """Get items within a price range."""
        return self.search(SearchFilters(
            min_price=min_price,
            max_price=max_price
        ))

    def get_all_categories(self) -> List[str]:
        """Get all unique categories."""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT category
            FROM menu_items
            ORDER BY category
        ''')
        return [row['category'] for row in cursor.fetchall()]

    def get_all_sizes(self) -> List[str]:
        """Get all unique size names."""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT name
            FROM drink_sizes
            ORDER BY name
        ''')
        return [row['name'] for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the database."""
        cursor = self.db.conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM locations')
        location_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM menu_items')
        item_count = cursor.fetchone()['count']

        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM menu_items
            GROUP BY category
            ORDER BY count DESC
        ''')
        category_stats = [
            {'category': row['category'], 'count': row['count']}
            for row in cursor.fetchall()
        ]

        cursor.execute('''
            SELECT AVG(base_price) as avg_price,
                   MIN(base_price) as min_price,
                   MAX(base_price) as max_price
            FROM menu_items
            WHERE base_price IS NOT NULL
        ''')
        price_stats = cursor.fetchone()

        return {
            'total_locations': location_count,
            'total_items': item_count,
            'categories': category_stats,
            'price_stats': {
                'average': round(price_stats['avg_price'], 2) if price_stats['avg_price'] else 0,
                'min': price_stats['min_price'],
                'max': price_stats['max_price']
            }
        }

    def close(self):
        """Close the database connection."""
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
