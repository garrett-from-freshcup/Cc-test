"""
Storage module for persisting cafe menu data to SQLite database.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import CafeMenu, CafeLocation, MenuItem, DrinkSize


class MenuDatabase:
    """SQLite database for storing and retrieving cafe menu data."""

    def __init__(self, db_path: str = 'cafe_menus.db'):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                url TEXT UNIQUE,
                phone TEXT,
                hours TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                base_price REAL,
                scraped_at TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drink_sizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                volume TEXT,
                FOREIGN KEY (item_id) REFERENCES menu_items(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_location
            ON menu_items(location_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_category
            ON menu_items(category)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_name
            ON menu_items(name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sizes_item
            ON drink_sizes(item_id)
        ''')

        self.conn.commit()

    def save_menu(self, menu: CafeMenu) -> int:
        """
        Save a cafe menu to the database.

        Args:
            menu: The CafeMenu to save

        Returns:
            The location_id of the saved menu
        """
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT id FROM locations WHERE url = ?
        ''', (menu.location.url,))

        result = cursor.fetchone()

        if result:
            location_id = result[0]
            cursor.execute('''
                UPDATE locations
                SET name = ?, address = ?, city = ?, state = ?, zip_code = ?,
                    phone = ?, hours = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                menu.location.name,
                menu.location.address,
                menu.location.city,
                menu.location.state,
                menu.location.zip_code,
                menu.location.phone,
                menu.location.hours,
                location_id
            ))

            cursor.execute('DELETE FROM menu_items WHERE location_id = ?', (location_id,))
        else:
            cursor.execute('''
                INSERT INTO locations (name, address, city, state, zip_code, url, phone, hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                menu.location.name,
                menu.location.address,
                menu.location.city,
                menu.location.state,
                menu.location.zip_code,
                menu.location.url,
                menu.location.phone,
                menu.location.hours
            ))
            location_id = cursor.lastrowid

        for item in menu.items:
            cursor.execute('''
                INSERT INTO menu_items (location_id, name, category, description, base_price, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                location_id,
                item.name,
                item.category,
                item.description,
                item.base_price,
                menu.scraped_at
            ))
            item_id = cursor.lastrowid

            for size in item.sizes:
                cursor.execute('''
                    INSERT INTO drink_sizes (item_id, name, price, volume)
                    VALUES (?, ?, ?, ?)
                ''', (item_id, size.name, size.price, size.volume))

        self.conn.commit()
        return location_id

    def get_all_locations(self) -> List[CafeLocation]:
        """Get all cafe locations from the database."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM locations ORDER BY name')

        locations = []
        for row in cursor.fetchall():
            locations.append(CafeLocation(
                name=row['name'],
                address=row['address'],
                city=row['city'],
                state=row['state'],
                zip_code=row['zip_code'],
                url=row['url'],
                phone=row['phone'],
                hours=row['hours']
            ))

        return locations

    def get_menu_by_location_id(self, location_id: int) -> Optional[CafeMenu]:
        """Get a complete menu for a specific location."""
        cursor = self.conn.cursor()

        cursor.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
        location_row = cursor.fetchone()

        if not location_row:
            return None

        location = CafeLocation(
            name=location_row['name'],
            address=location_row['address'],
            city=location_row['city'],
            state=location_row['state'],
            zip_code=location_row['zip_code'],
            url=location_row['url'],
            phone=location_row['phone'],
            hours=location_row['hours']
        )

        cursor.execute('''
            SELECT * FROM menu_items
            WHERE location_id = ?
            ORDER BY category, name
        ''', (location_id,))

        items = []
        for item_row in cursor.fetchall():
            cursor.execute('''
                SELECT * FROM drink_sizes WHERE item_id = ?
            ''', (item_row['id'],))

            sizes = [
                DrinkSize(
                    name=size_row['name'],
                    price=size_row['price'],
                    volume=size_row['volume']
                )
                for size_row in cursor.fetchall()
            ]

            items.append(MenuItem(
                name=item_row['name'],
                category=item_row['category'],
                description=item_row['description'],
                sizes=sizes,
                base_price=item_row['base_price']
            ))

        scraped_at = datetime.now()
        if items:
            cursor.execute('''
                SELECT MAX(scraped_at) as latest
                FROM menu_items
                WHERE location_id = ?
            ''', (location_id,))
            result = cursor.fetchone()
            if result['latest']:
                scraped_at = datetime.fromisoformat(result['latest'])

        return CafeMenu(location=location, items=items, scraped_at=scraped_at)

    def get_menu_by_url(self, url: str) -> Optional[CafeMenu]:
        """Get a menu by the cafe's URL."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM locations WHERE url = ?', (url,))
        result = cursor.fetchone()

        if result:
            return self.get_menu_by_location_id(result['id'])
        return None

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
