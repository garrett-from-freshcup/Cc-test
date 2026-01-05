#!/usr/bin/env python3
"""
Command-line interface for the Cafe Menu Scraper tool.
"""

import argparse
import sys
import json
from typing import Optional

from cafe_scraper.scraper import SquareScraper
from cafe_scraper.cleaner import MenuCleaner
from cafe_scraper.storage import MenuDatabase
from cafe_scraper.search import MenuSearcher, SearchFilters


def scrape_command(args):
    """Scrape a cafe menu from a URL."""
    print(f"Scraping menu from: {args.url}")

    scraper = SquareScraper()
    menu = scraper.scrape_menu(args.url)

    if not menu:
        print("Failed to scrape menu.")
        return 1

    print(f"Found {len(menu.items)} items at {menu.location.name}")

    if args.clean:
        print("Cleaning and normalizing data...")
        cleaner = MenuCleaner()
        menu = cleaner.clean_menu(menu)

    if args.save:
        print("Saving to database...")
        db = MenuDatabase(args.database)
        location_id = db.save_menu(menu)
        db.close()
        print(f"Saved menu (location_id: {location_id})")

    if args.output:
        print(f"Writing to {args.output}...")
        with open(args.output, 'w') as f:
            json.dump(menu.to_dict(), f, indent=2)

    if not args.save and not args.output:
        print("\nMenu Preview:")
        print(json.dumps(menu.to_dict(), indent=2))

    return 0


def search_command(args):
    """Search for menu items."""
    filters = SearchFilters(
        query=args.query,
        category=args.category,
        size=args.size,
        min_price=args.min_price,
        max_price=args.max_price,
        city=args.city,
        state=args.state,
        location_name=args.location
    )

    with MenuSearcher(args.database) as searcher:
        results = searcher.search(filters)

        if not results:
            print("No items found matching your criteria.")
            return 0

        print(f"\nFound {len(results)} items:\n")

        for item in results:
            print(f"{item['name']} - {item['category']}")
            print(f"  Location: {item['location']['name']}, {item['location']['city']}, {item['location']['state']}")

            if item['description']:
                print(f"  Description: {item['description']}")

            if item['sizes']:
                print("  Sizes:")
                for size in item['sizes']:
                    volume = f" ({size['volume']})" if size['volume'] else ""
                    print(f"    - {size['name']}: ${size['price']:.2f}{volume}")
            elif item['base_price']:
                print(f"  Price: ${item['base_price']:.2f}")

            print()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}")

    return 0


def list_command(args):
    """List locations or categories."""
    db = MenuDatabase(args.database)

    if args.type == 'locations':
        locations = db.get_all_locations()
        print(f"\nFound {len(locations)} locations:\n")

        for loc in locations:
            print(f"{loc.name}")
            print(f"  {loc.address}, {loc.city}, {loc.state} {loc.zip_code}")
            if loc.phone:
                print(f"  Phone: {loc.phone}")
            if loc.url:
                print(f"  URL: {loc.url}")
            print()

    elif args.type == 'categories':
        with MenuSearcher(args.database) as searcher:
            categories = searcher.get_all_categories()
            print(f"\nFound {len(categories)} categories:\n")
            for cat in categories:
                print(f"  - {cat}")

    elif args.type == 'sizes':
        with MenuSearcher(args.database) as searcher:
            sizes = searcher.get_all_sizes()
            print(f"\nFound {len(sizes)} drink sizes:\n")
            for size in sizes:
                print(f"  - {size}")

    db.close()
    return 0


def stats_command(args):
    """Show database statistics."""
    with MenuSearcher(args.database) as searcher:
        stats = searcher.get_statistics()

        print("\nDatabase Statistics:\n")
        print(f"Total Locations: {stats['total_locations']}")
        print(f"Total Menu Items: {stats['total_items']}")

        print(f"\nPrice Statistics:")
        print(f"  Average: ${stats['price_stats']['average']:.2f}")
        print(f"  Min: ${stats['price_stats']['min']:.2f}")
        print(f"  Max: ${stats['price_stats']['max']:.2f}")

        print(f"\nItems by Category:")
        for cat in stats['categories']:
            print(f"  {cat['category']}: {cat['count']}")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Cafe Menu Scraper - Scrape and search cafe menus from Square ordering websites'
    )

    parser.add_argument(
        '--database',
        default='cafe_menus.db',
        help='Path to SQLite database file (default: cafe_menus.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    scrape_parser = subparsers.add_parser('scrape', help='Scrape a cafe menu')
    scrape_parser.add_argument('url', help='URL of the Square ordering website')
    scrape_parser.add_argument('--clean', action='store_true', help='Clean and normalize data')
    scrape_parser.add_argument('--save', action='store_true', help='Save to database')
    scrape_parser.add_argument('--output', help='Save to JSON file')

    search_parser = subparsers.add_parser('search', help='Search menu items')
    search_parser.add_argument('--query', help='Text search query')
    search_parser.add_argument('--category', help='Filter by category')
    search_parser.add_argument('--size', help='Filter by drink size')
    search_parser.add_argument('--min-price', type=float, help='Minimum price')
    search_parser.add_argument('--max-price', type=float, help='Maximum price')
    search_parser.add_argument('--city', help='Filter by city')
    search_parser.add_argument('--state', help='Filter by state')
    search_parser.add_argument('--location', help='Filter by location name')
    search_parser.add_argument('--output', help='Save results to JSON file')

    list_parser = subparsers.add_parser('list', help='List locations, categories, or sizes')
    list_parser.add_argument(
        'type',
        choices=['locations', 'categories', 'sizes'],
        help='What to list'
    )

    stats_parser = subparsers.add_parser('stats', help='Show database statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'scrape':
        return scrape_command(args)
    elif args.command == 'search':
        return search_command(args)
    elif args.command == 'list':
        return list_command(args)
    elif args.command == 'stats':
        return stats_command(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
