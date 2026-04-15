# Comix.to Scraper

This is a comprehensive Python script to scrape and download manga from `comix.to`. It natively handles Cloudflare protection by intercepting API calls via Playwright, and saves the manga chapters perfectly as continuous-scroll PDFs with no visible page divisions.

## Features

- **Robust Scraping:** Uses `playwright` to seamlessly browse the website and securely intercept backend JSON routes without triggering bot protection.
- **Smart Tracking:** Maintains a real-time append-only `manga_log.csv` file. It records manga metadata (ID, titles, author, genre, release date) and ensures that you *never* download the same manga twice across different runs.
- **Continuous PDFs:** Uses `img2pdf` to package downloaded `.webp` and `.jpg` image panels into a single PDF tailored for smooth vertical reading, with no margins or gaps between pages.
- **Organized Storage:** Automatically organizes downloads into directories based on the manga's primary genre (`Downloads/<Genre>/<Manga_Title>/`).
- **Resilient:** Supports customizable rate-limiting, retries, concurrency, and keeps an `error.log` of any failures.

## Prerequisites

1. Ensure you have Python 3 installed.
2. Install the required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

3. Install the Playwright Chromium browser binary:

```bash
playwright install chromium
```

## Usage

Run the scraper from the command line:

```bash
python comix_scraper.py
```

### CLI Arguments

You can customize the script's behavior using the following optional arguments:

- `--concurrency`: Number of concurrent image downloads per chapter. (Default: `1`)
- `--delay`: Delay in seconds between image downloads to prevent rate-limiting. (Default: `0.5`)
- `--limit-manga`: The maximum number of manga to process in a single run. Use `0` to scrape everything found. (Default: `0`)
- `--limit-chapters`: The maximum number of chapters to process per manga. Use `0` to download all available chapters. (Default: `0`)

#### Examples

**Test Run (Download only 1 manga, and only 1 chapter of it):**
```bash
python comix_scraper.py --limit-manga 1 --limit-chapters 1
```

**Fast Concurrent Download:**
```bash
python comix_scraper.py --concurrency 5 --delay 0.1
```

## Output Structure

The script will automatically create a `Downloads` directory in the same folder, organizing the manga by genre.

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
