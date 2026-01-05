"""
Web interface for the Cafe Menu Scraper tool.
Run this to start the web interface - no terminal knowledge needed!
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os

from cafe_scraper.scraper import SquareScraper
from cafe_scraper.cleaner import MenuCleaner
from cafe_scraper.storage import MenuDatabase
from cafe_scraper.search import MenuSearcher, SearchFilters

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = 'cafe_menus.db'


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Scrape a cafe menu."""
    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            flash('Please enter a URL', 'error')
            return redirect(url_for('scrape'))

        try:
            scraper = SquareScraper()
            menu = scraper.scrape_menu(url)

            if not menu:
                flash('Failed to scrape menu. Please check the URL.', 'error')
                return redirect(url_for('scrape'))

            cleaner = MenuCleaner()
            menu = cleaner.clean_menu(menu)

            db = MenuDatabase(DB_PATH)
            location_id = db.save_menu(menu)
            db.close()

            flash(f'Successfully scraped {len(menu.items)} items from {menu.location.name}!', 'success')
            return redirect(url_for('locations'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('scrape'))

    return render_template('scrape.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search menu items."""
    results = []
    filters_applied = {}

    if request.method == 'POST' or request.args:
        data = request.form if request.method == 'POST' else request.args

        query = data.get('query', '').strip() or None
        category = data.get('category', '').strip() or None
        size = data.get('size', '').strip() or None
        city = data.get('city', '').strip() or None
        state = data.get('state', '').strip() or None
        location = data.get('location', '').strip() or None

        min_price = None
        max_price = None

        if data.get('min_price'):
            try:
                min_price = float(data.get('min_price'))
            except ValueError:
                pass

        if data.get('max_price'):
            try:
                max_price = float(data.get('max_price'))
            except ValueError:
                pass

        filters = SearchFilters(
            query=query,
            category=category,
            size=size,
            min_price=min_price,
            max_price=max_price,
            city=city,
            state=state,
            location_name=location
        )

        filters_applied = {k: v for k, v in {
            'query': query,
            'category': category,
            'size': size,
            'city': city,
            'state': state,
            'location': location,
            'min_price': min_price,
            'max_price': max_price
        }.items() if v}

        try:
            with MenuSearcher(DB_PATH) as searcher:
                results = searcher.search(filters)
        except Exception as e:
            flash(f'Error searching: {str(e)}', 'error')

    try:
        with MenuSearcher(DB_PATH) as searcher:
            categories = searcher.get_all_categories()
            sizes = searcher.get_all_sizes()
    except:
        categories = []
        sizes = []

    return render_template(
        'search.html',
        results=results,
        filters=filters_applied,
        categories=categories,
        sizes=sizes
    )


@app.route('/locations')
def locations():
    """List all cafe locations."""
    try:
        db = MenuDatabase(DB_PATH)
        locs = db.get_all_locations()
        db.close()
        return render_template('locations.html', locations=locs)
    except Exception as e:
        flash(f'Error loading locations: {str(e)}', 'error')
        return render_template('locations.html', locations=[])


@app.route('/location/<int:location_id>')
def location_menu(location_id):
    """View menu for a specific location."""
    try:
        db = MenuDatabase(DB_PATH)
        menu = db.get_menu_by_location_id(location_id)
        db.close()

        if not menu:
            flash('Location not found', 'error')
            return redirect(url_for('locations'))

        items_by_category = {}
        for item in menu.items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)

        return render_template(
            'location_menu.html',
            location=menu.location,
            items_by_category=items_by_category
        )
    except Exception as e:
        flash(f'Error loading menu: {str(e)}', 'error')
        return redirect(url_for('locations'))


@app.route('/stats')
def stats():
    """Show database statistics."""
    try:
        with MenuSearcher(DB_PATH) as searcher:
            statistics = searcher.get_statistics()
        return render_template('stats.html', stats=statistics)
    except Exception as e:
        flash(f'Error loading statistics: {str(e)}', 'error')
        return render_template('stats.html', stats=None)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Cafe Menu Scraper - Web Interface")
    print("="*60)
    print("\n  The web interface is starting...")
    print("\n  Once it's ready, open your web browser and go to:")
    print("\n      http://localhost:5000")
    print("\n  Press CTRL+C to stop the server")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
