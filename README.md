# Comix.to Scraper (Google Colab & Google Drive Edition)

This is an asynchronous Python scraper to seamlessly download manga from `comix.to` directly from a Google Colab notebook environment. **It is specifically designed to store all data directly into your Google Drive, bypassing Colab's unreliable local disk storage entirely.**

## Features

- **Direct Google Drive Storage:** The script detects if it is running in Google Colab. If it is, it mounts your Google Drive and saves *everything* (PDFs, logs, and CSV) directly to `/content/drive/MyDrive/ComixScraper/`.
- **Zero Local Disk Footprint:** Raw WebP image downloads are buffered entirely in-memory using `BytesIO`. The images are merged and saved directly as a PDF to Google Drive without ever writing intermediate files to Colab's disk.
- **Robust Scraping:** Bypasses API blocks using headless Chromium, allowing secure interception of JSON chapter data.
- **Smart Tracking:** Maintains a real-time append-only `manga_log.csv` file directly on your Drive. It records manga metadata (ID, titles, author, genre, release date) and ensures that you *never* download the same manga twice across different runs.
- **Continuous PDFs:** Packages downloaded `.webp` and `.jpg` image panels into a single PDF perfectly tailored for smooth vertical reading (webtoons/manhwa) using `img2pdf` with zero margins.
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

When you run the script for the first time, a popup will appear asking you to authorize Google Colab to access your Google Drive. Click **Allow**.

```python
!python comix_scraper.py --concurrency 5 --delay 0.1 --limit-manga 5
```

Alternatively, you can just paste the entire `comix_scraper.py` source code into a Jupyter Notebook cell and execute it directly.

### CLI Arguments

You can customize the script's behavior using the following optional arguments:

- `--concurrency`: Number of concurrent image downloads per chapter. (Default: `5`)
- `--delay`: Delay in seconds between concurrent image download batches. (Default: `0.2`)
- `--limit-manga`: The maximum number of manga to process in a single run. Use `0` to scrape everything found. (Default: `0`)
- `--limit-chapters`: The maximum number of chapters to process per manga. Use `0` to download all available chapters. (Default: `0`)

## Output Structure

The script will automatically create a `ComixScraper` directory in your Google Drive root.

```
/content/drive/MyDrive/ComixScraper/
├── manga_log.csv
├── error.log
└── Downloads/
    ├── Action/
    │   └── Eleceed/
    │       ├── 397.Eleceed.pdf
    │       └── 398.Eleceed.pdf
    └── Romance/
        └── 19 Days/
            └── 459.19 Days.pdf
```

Because everything is saved directly to your Google Drive, you will not lose any data if the Google Colab runtime crashes or disconnects!
