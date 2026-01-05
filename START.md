# 🚀 How to Start the Cafe Menu Scraper

## Super Simple Instructions (No Technical Knowledge Needed!)

### Step 1: Install Python (One-Time Setup)

1. Go to https://www.python.org/downloads/
2. Download Python (any version 3.7 or newer)
3. Run the installer
4. **IMPORTANT:** Check the box that says "Add Python to PATH" during installation
5. Click "Install Now"

### Step 2: Install Dependencies (One-Time Setup)

#### On Windows:
1. Open the folder where you downloaded this tool
2. Double-click the file named `SETUP-WINDOWS.bat`
3. Wait for it to finish (it will install everything you need)

#### On Mac/Linux:
1. Open the folder where you downloaded this tool
2. Double-click the file named `SETUP-MAC.command` (Mac) or `SETUP-LINUX.sh` (Linux)
3. Wait for it to finish

### Step 3: Start the Web Interface

#### On Windows:
1. Double-click the file named `START-WINDOWS.bat`
2. A black window will appear - **DON'T CLOSE IT!**
3. Your web browser should open automatically
4. If it doesn't, open your browser and go to: http://localhost:5000

#### On Mac/Linux:
1. Double-click the file named `START-MAC.command` (Mac) or `START-LINUX.sh` (Linux)
2. A terminal window will appear - **DON'T CLOSE IT!**
3. Your web browser should open automatically
4. If it doesn't, open your browser and go to: http://localhost:5000

### Step 4: Use the Tool!

Once the web page opens, you'll see a simple interface with buttons:

1. **Add Cafe** - Enter a Square ordering website URL to scrape menus
2. **Search Items** - Find specific drinks or food items
3. **View Cafes** - See all the cafes you've added
4. **Statistics** - View cool stats about your database

### How to Stop

Just close the black window (Windows) or terminal window (Mac/Linux) that appeared when you started the tool.

---

## Troubleshooting

**Problem: "Python is not recognized"**
- Solution: You need to install Python (see Step 1) and make sure to check "Add Python to PATH"

**Problem: Web page won't load**
- Solution: Make sure the black/terminal window is still open. That needs to stay open while you use the tool.

**Problem: I can't find the startup files**
- Solution: They should be in the same folder as this document. If you don't see .bat or .command files, you can run the tool manually (see below).

---

## Manual Start (If the startup scripts don't work)

### Windows:
1. Open Command Prompt in the tool's folder
2. Type: `pip install -r requirements.txt` (press Enter)
3. Type: `python web_app.py` (press Enter)
4. Open your browser to http://localhost:5000

### Mac/Linux:
1. Open Terminal in the tool's folder
2. Type: `pip install -r requirements.txt` (press Enter)
3. Type: `python web_app.py` (press Enter)
4. Open your browser to http://localhost:5000

---

## Need Help?

If you're still stuck, contact your technical friend or check the README.md file for more detailed information.
