import asyncio
import json
from playwright.async_api import async_playwright # type: ignore
from typing import List
import time

BASE_URL = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"

async def scrape():
    data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(BASE_URL)

        while True:
            # Wait for products to load
            await page.wait_for_selector('.thumbnail')

            products = await page.query_selector_all('.thumbnail')

            for product in products:
                title_elem = await product.query_selector('a.title')
                title = await title_elem.inner_text()
                product_url = await title_elem.get_attribute('href')
                full_product_url = f"https://webscraper.io{product_url}"

                price = await (await product.query_selector('.price')).inner_text()
                rating = len(await product.query_selector_all('div.ratings span.ws-icon.ws-icon-star'))
                reviews_text = await (await product.query_selector('.ratings p')).inner_text()
                reviews_count = int(reviews_text.strip().split()[0])

                # Visit product detail page
                description = ""
                try:
                    detail_page = await context.new_page()
                    await detail_page.goto(full_product_url)
                    await detail_page.wait_for_selector('.description')
                    description = await (await detail_page.query_selector('.description')).inner_text()
                    await detail_page.close()
                except Exception as e:
                    print(f"Error fetching description: {e}")

                data.append({
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "product_url": full_product_url,
                    "description": description
                })

            # Check for next page
            next_button = await page.query_selector('.pagination li.next a')
            if next_button:
                try:
                    await next_button.click()
                    await page.wait_for_timeout(1000)
                except:
                    break
            else:
                break

        # Save to JSON
        with open("output.json", "w") as f:
            json.dump(data, f, indent=4)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape())