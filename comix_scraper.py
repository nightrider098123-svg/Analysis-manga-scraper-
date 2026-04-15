import argparse
import csv
import logging
import os
import re
import asyncio
import aiohttp
from io import BytesIO
from playwright.async_api import async_playwright
import img2pdf
from PIL import Image

import nest_asyncio
nest_asyncio.apply()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
error_logger = logging.getLogger('error_logger')
error_handler = logging.FileHandler('error.log')
error_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
error_logger.addHandler(error_handler)

CSV_FILE = "manga_log.csv"
BASE_DIR = "Downloads"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "english_title", "japanese_title", "author", "genre", "release_date", "recommendations"])

def load_downloaded_mangas():
    downloaded = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                downloaded.add(str(row["id"]))
    return downloaded

def log_manga(manga_data):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            manga_data.get("id", ""),
            manga_data.get("english_title", ""),
            manga_data.get("japanese_title", ""),
            manga_data.get("author", ""),
            manga_data.get("genre", ""),
            manga_data.get("release_date", ""),
            manga_data.get("recommendations", "")
        ])

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

async def download_image(session, url, delay=0, retries=3):
    headers = {"User-Agent": "Mozilla/5.0"}
    if delay > 0:
        await asyncio.sleep(delay)
    for attempt in range(retries):
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            if attempt == retries - 1:
                error_logger.error(f"Failed to download image {url}: {e}")
            await asyncio.sleep(1)
    return None

def create_pdf(images_data, pdf_path):
    valid_images = []
    for data in images_data:
        try:
            img = Image.open(BytesIO(data))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_io = BytesIO()
            img.save(img_io, format="JPEG")
            valid_images.append(img_io.getvalue())
        except Exception as e:
            error_logger.error(f"Failed to process image for PDF {pdf_path}: {e}")
            continue

    if valid_images:
        try:
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(valid_images))
            return True
        except Exception as e:
            error_logger.error(f"Failed to save PDF {pdf_path}: {e}")
            return False
    return False

async def scrape_manga_chapter(page, browser_context, manga_data, chapter, args):
    ch_number = str(chapter.get("number", "Unknown")).replace('.0', '')
    ch_id = chapter.get("chapter_id", "")

    slug = manga_data.get("slug", "manga")
    hash_id = manga_data.get("hash_id", "id")
    manga_title = sanitize_filename(manga_data.get("english_title") or manga_data.get("japanese_title", "Unknown"))

    chapter_url = f"https://comix.to/title/{hash_id}-{slug}/{ch_id}-chapter-{ch_number}"

    genre = sanitize_filename(manga_data.get("genre", "Uncategorized").split(',')[0].strip())
    if not genre:
        genre = "Uncategorized"

    manga_dir = os.path.join(BASE_DIR, genre, manga_title)
    os.makedirs(manga_dir, exist_ok=True)

    pdf_filename = f"{ch_number}.{manga_title}.pdf"
    pdf_path = os.path.join(manga_dir, pdf_filename)

    if os.path.exists(pdf_path):
        logging.info(f"Chapter {ch_number} already exists, skipping.")
        return

    logging.info(f"Scraping chapter {ch_number}: {chapter_url}")

    for attempt in range(3):
        try:
            await page.goto(chapter_url, wait_until="networkidle", timeout=30000)
            break
        except Exception as e:
            logging.warning(f"Timeout on chapter page, retrying...")
            await asyncio.sleep(2)

    html = await page.content()

    image_urls = re.findall(r'https:\/\/[^"]+\.wowpic[0-9]*\.store[^"]+\.(?:webp|jpg|png)', html)
    unique_urls = []
    seen = set()
    for u in image_urls:
        if '@' in u:
            continue
        u = u.replace('\\/', '/')
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    if not unique_urls:
        error_logger.error(f"No images found for {manga_title} chapter {ch_number}")
        return

    logging.info(f"Found {len(unique_urls)} images. Downloading with concurrency {args.concurrency}...")

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(args.concurrency)

        async def fetch(url, delay):
            async with semaphore:
                return await download_image(session, url, delay=delay)

        tasks = [fetch(url, args.delay) for url in unique_urls]
        images_data = await asyncio.gather(*tasks)

    images_data = [d for d in images_data if d is not None]
    if len(images_data) > 0:
        success = create_pdf(images_data, pdf_path)
        if success:
            logging.info(f"Saved {pdf_path}")
        else:
            error_logger.error(f"Failed to create PDF {pdf_path}")
    else:
        error_logger.error(f"All image downloads failed for chapter {ch_number}")

async def process_manga(manga, page, browser_context, args, downloaded_ids):
    manga_id = str(manga.get("manga_id", manga.get("id")))
    if manga_id in downloaded_ids:
        logging.info(f"Skipping manga {manga_id} (already downloaded).")
        return

    english_title = manga.get("title", "")
    alt_titles = manga.get("alt_titles", [])
    japanese_title = alt_titles[0] if alt_titles and len(alt_titles) > 0 else ""

    term_ids = manga.get("term_ids", [])
    genre = f"Genre_{term_ids[0]}" if term_ids else "Uncategorized"

    manga_data = {
        "id": manga_id,
        "english_title": english_title,
        "japanese_title": japanese_title,
        "author": "Unknown",
        "genre": genre,
        "release_date": manga.get("year", ""),
        "recommendations": "",
        "slug": manga.get("slug", ""),
        "hash_id": manga.get("hash_id", "")
    }

    logging.info(f"Processing Manga: {english_title} ({manga_id})")

    chapters = []

    async def handle_response(response):
        if '/api/v2/manga/' in response.url and '/chapters' in response.url:
            try:
                data = await response.json()
                if 'result' in data and 'items' in data['result']:
                    chapters.extend(data['result']['items'])
            except:
                pass

    page.on("response", handle_response)

    manga_url = f"https://comix.to/title/{manga.get('hash_id')}-{manga.get('slug')}"
    logging.info(f"Fetching chapter list from {manga_url}")
    await page.goto(manga_url, wait_until="networkidle")

    await page.evaluate("window.scrollBy(0, 1000);")
    await asyncio.sleep(3)

    page.remove_listener("response", handle_response)

    if not chapters:
        error_logger.error(f"No chapters found for {english_title} ({manga_id})")
        return

    logging.info(f"Found {len(chapters)} chapters.")

    chapters_to_process = chapters
    if args.limit_chapters:
        chapters_to_process = chapters[:args.limit_chapters]

    for ch in chapters_to_process:
        await scrape_manga_chapter(page, browser_context, manga_data, ch, args)

    log_manga(manga_data)
    downloaded_ids.add(manga_id)
    logging.info(f"Manga {english_title} completed and logged.")

async def async_main(args):
    init_csv()
    downloaded_ids = load_downloaded_mangas()

    logging.info("Starting scraper...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        mangas = []

        async def scrape_manga_list(response):
            if '/api/v2/manga' in response.url and 'chapters' not in response.url and 'search' not in response.url:
                try:
                    data = await response.json()
                    if 'result' in data and 'items' in data['result']:
                        mangas.extend(data['result']['items'])
                except:
                    pass

        page.on("response", scrape_manga_list)

        logging.info("Browsing library to find manga...")
        await page.goto("https://comix.to/browser?types=manga,manhwa,manhua", wait_until="networkidle")
        await asyncio.sleep(3)
        page.remove_listener("response", scrape_manga_list)

        logging.info(f"Discovered {len(mangas)} manga entries on the first page.")

        unique_mangas = {}
        for m in mangas:
            mid = m.get("manga_id", m.get("id"))
            if mid:
                unique_mangas[mid] = m

        mangas = list(unique_mangas.values())

        if args.limit_manga > 0:
            mangas = mangas[:args.limit_manga]

        for manga in mangas:
            await process_manga(manga, page, context, args, downloaded_ids)

        await browser.close()

    logging.info("Scraping completed.")

def main():
    parser = argparse.ArgumentParser(description="Comix.to Scraper for Google Colab")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent image downloads")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between image downloads in seconds")
    parser.add_argument("--limit-manga", type=int, default=0, help="Limit number of manga to process (0 = all)")
    parser.add_argument("--limit-chapters", type=int, default=0, help="Limit number of chapters to process per manga (0 = all)")

    # In Jupyter/Colab, sys.argv might contain stuff we don't want.
    # So we parse known args or provide defaults if ran without explicit args.
    import sys
    if 'ipykernel' in sys.modules:
        args, _ = parser.parse_known_args()
        # Set some sane test limits if running interactively in Colab without CLI flags
        if not any(arg.startswith('--') for arg in sys.argv):
            args.limit_manga = 1
            args.limit_chapters = 2
    else:
        args = parser.parse_args()

    asyncio.run(async_main(args))

if __name__ == "__main__":
    main()
