# Cafe Menu Scraper

A Python tool that scrapes cafe menu data from Square ordering websites, cleans and normalizes the data, and provides powerful search and filter functionality.

## Features

- **Web Scraping**: Extracts menu data from Square online ordering websites
- **Data Normalization**: Cleans and standardizes menu items, prices, sizes, and categories
- **SQLite Storage**: Persists data in a lightweight, portable database
- **Advanced Search**: Filter and search by:
  - Drink size (Small, Medium, Large, etc.)
  - Cafe location (city, state, name)
  - Category (Coffee, Tea, Pastries, etc.)
  - Price range
  - Text search (item names and descriptions)
- **CLI Interface**: Easy-to-use command-line tool

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Cc-test
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Scraping a Cafe Menu

Scrape a menu from a Square ordering website:

```bash
python cli.py scrape <URL> --clean --save
```

Options:
- `--clean`: Clean and normalize the scraped data
- `--save`: Save to the database
- `--output <file>`: Save raw data to a JSON file

Example:
```bash
python cli.py scrape https://square.site/example-cafe --clean --save
```

### Searching Menu Items

Search for items with various filters:

```bash
# Search by text
python cli.py search --query "latte"

# Filter by drink size
python cli.py search --size "large"

# Filter by location
python cli.py search --city "Seattle" --state "WA"

# Filter by category
python cli.py search --category "coffee"

# Filter by price range
python cli.py search --min-price 3.00 --max-price 6.00

# Combine multiple filters
python cli.py search --query "mocha" --size "medium" --city "Portland"

# Save results to file
python cli.py search --category "espresso" --output results.json
```

### Listing Data

List all locations, categories, or sizes in the database:

```bash
# List all cafe locations
python cli.py list locations

# List all menu categories
python cli.py list categories

# List all available drink sizes
python cli.py list sizes
```

### Database Statistics

View statistics about your scraped data:

```bash
python cli.py stats
```

This shows:
- Total number of locations
- Total number of menu items
- Price statistics (min, max, average)
- Items per category

## Project Structure

```
Cc-test/
├── cafe_scraper/
│   ├── __init__.py          # Package initialization
│   ├── models.py            # Data models (MenuItem, CafeLocation, etc.)
│   ├── scraper.py           # Web scraping logic for Square sites
│   ├── cleaner.py           # Data cleaning and normalization
│   ├── storage.py           # SQLite database operations
│   └── search.py            # Search and filter functionality
├── cli.py                   # Command-line interface
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Database Schema

The tool uses SQLite with three main tables:

- **locations**: Cafe information (name, address, city, state, phone, hours)
- **menu_items**: Menu items (name, category, description, base_price)
- **drink_sizes**: Size options for each item (name, price, volume)

## Data Normalization

The cleaner module automatically:
- Standardizes size names (sm → Small, lg → Large, etc.)
- Normalizes categories (latte → Coffee, smoothie → Smoothies)
- Removes duplicate items and sizes
- Extracts volume information (12oz, 16oz, etc.)
- Cleans text and removes special characters
- Rounds prices to 2 decimal places

## Examples

### Example 1: Build a Local Cafe Database

```bash
# Scrape multiple cafes
python cli.py scrape https://square.site/cafe1 --clean --save
python cli.py scrape https://square.site/cafe2 --clean --save
python cli.py scrape https://square.site/cafe3 --clean --save

# View all locations
python cli.py list locations

# See what you have
python cli.py stats
```

### Example 2: Find the Cheapest Lattes

```bash
python cli.py search --query "latte" --max-price 5.00
```

### Example 3: Find All Large Drinks in a City

```bash
python cli.py search --size "large" --city "Portland"
```

### Example 4: Export All Coffee Items

```bash
python cli.py search --category "coffee" --output coffee_menu.json
```

## Programmatic Usage

You can also use the modules directly in Python:

```python
from cafe_scraper.scraper import SquareScraper
from cafe_scraper.cleaner import MenuCleaner
from cafe_scraper.storage import MenuDatabase
from cafe_scraper.search import MenuSearcher, SearchFilters

# Scrape a menu
scraper = SquareScraper()
menu = scraper.scrape_menu('https://square.site/example-cafe')

# Clean the data
cleaner = MenuCleaner()
menu = cleaner.clean_menu(menu)

# Save to database
db = MenuDatabase('cafe_menus.db')
db.save_menu(menu)
db.close()

# Search
searcher = MenuSearcher('cafe_menus.db')
results = searcher.search(SearchFilters(
    query='latte',
    size='medium',
    max_price=6.00
))
searcher.close()
```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- lxml

## Notes

- The scraper is designed for Square ordering websites but may work with other similar platforms
- Some sites may have anti-scraping measures; use responsibly
- Always respect websites' terms of service and robots.txt
- Data accuracy depends on the website's structure and may vary

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
