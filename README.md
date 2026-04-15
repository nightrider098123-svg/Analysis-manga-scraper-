# Comix.to Scraper (Google Colab Edition)

This is an asynchronous Python scraper to seamlessly download manga from `comix.to` directly from a Google Colab notebook environment. It uses `playwright` to natively handle the site's Cloudflare protection and `aiohttp` to concurrently download raw manga image panels. Finally, it uses `img2pdf` to output continuous-scroll PDFs with zero visible gaps between images.

## Features

- **Google Colab Native:** Designed with `nest_asyncio` and `async_playwright` so it runs perfectly in Jupyter Notebook/Colab cells.
- **Robust Scraping:** Bypasses API blocks using headless Chromium, allowing secure interception of JSON chapter data.
- **Smart Tracking:** Maintains a real-time append-only `manga_log.csv` file. It records manga metadata (ID, titles, author, genre, release date) and ensures that you *never* download the same manga twice across different runs.
- **Continuous PDFs:** Packages downloaded `.webp` and `.jpg` image panels into a single PDF perfectly tailored for smooth vertical reading (webtoons/manhwa).
- **Organized Storage:** Automatically organizes downloads into directories based on the manga's primary genre (`Downloads/<Genre>/<Manga_Title>/{Chapter}.{Title}.pdf`).

## Usage in Google Colab

Follow these steps exactly to run the scraper directly in Google Colab:

### Step 1: Install Dependencies
Create the first cell in your Colab notebook and run the following command to install required Python libraries and the Playwright Ubuntu dependencies:

```python
!pip install nest_asyncio playwright requests aiohttp PyMuPDF Pillow img2pdf
!playwright install chromium
!playwright install-deps
```

### Step 2: Upload and Run the Script
Create a second cell, upload `comix_scraper.py` to your Colab `/content/` directory, and run the script.

By default, without passing arguments, it is designed to scrape a small amount of data to test. You should pass CLI arguments to run it fully:

```python
!python comix_scraper.py --concurrency 5 --delay 0.1 --limit-manga 5
```

If you want to run the python code directly inside a Jupyter Notebook cell instead of a separate `.py` file, you can simply paste the entire contents of `comix_scraper.py` into a notebook cell and execute it. The `nest_asyncio.apply()` function at the top will automatically patch the event loop for you.

### CLI Arguments

You can customize the script's behavior using the following optional arguments:

- `--concurrency`: Number of concurrent image downloads per chapter. (Default: `5`)
- `--delay`: Delay in seconds between concurrent image download batches. (Default: `0.2`)
- `--limit-manga`: The maximum number of manga to process in a single run. Use `0` to scrape everything found. (Default: `0`)
- `--limit-chapters`: The maximum number of chapters to process per manga. Use `0` to download all available chapters. (Default: `0`)

## Output Structure

The script will automatically create a `Downloads` directory in the environment. In Google Colab, you will find this inside `/content/Downloads/`.

```
Downloads/
├── Action/
│   └── Eleceed/
│       ├── 397.Eleceed.pdf
│       └── 398.Eleceed.pdf
└── Romance/
    └── 19 Days/
        └── 459.19 Days.pdf
```

You can then zip the folder and download it, or sync it directly to Google Drive.
