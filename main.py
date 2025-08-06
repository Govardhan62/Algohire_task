import asyncio
import json
from playwright.async_api import async_playwright # type: ignore

async def scrape_flipkart_titles_and_prices():
    scraped_data = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://www.flipkart.com/search?q=mobiles")

        # Close login popup if it appears
        try:
            close_btn = await page.query_selector("button._2KpZ6l._2doB4z")
            if close_btn:
                await close_btn.click()
        except Exception:
            pass  # Popup not found

        page_number = 1

        while True:

            print(f"Scraping Page {page_number}...\n")
            await page.wait_for_selector("div.tUxRFH")

            products = await page.query_selector_all("div.tUxRFH")

            for idx, product in enumerate(products, 1):
                title_elem = await product.query_selector("div.KzDlHZ")
                price_elem = await product.query_selector("div.Nx9bqj._4b5DiR")
                rating_review_elem = await product.query_selector("span.Wphh3N")
                desc_elem = await product.query_selector("div._6NESgJ")

                title = await title_elem.inner_text() if title_elem else "No Title"
                price = await price_elem.inner_text() if price_elem else "No Price"
                description = await desc_elem.inner_text() if desc_elem else "No Description"
                description = description.replace("\n", " | ")


                # Split rating and review
                if rating_review_elem:
                    rating_review_text = await rating_review_elem.inner_text()
                    parts = rating_review_text.split('&')
                    rating = parts[0].strip() if len(parts) > 0 else "No Rating"
                    review = parts[1].strip() if len(parts) > 1 else "No Review"
                else:
                    rating = "No Rating"
                    review = "No Review"

                # Product URL
                link_elem = await product.query_selector("a")
                relative_url = await link_elem.get_attribute("href") if link_elem else None
                product_url = f"https://www.flipkart.com{relative_url}" if relative_url else "No URL"

                # Store in list
                scraped_data.append({
                    "title": title,
                    "price": price,
                    "description": description,
                    "rating": rating,
                    "reviews_count": review,
                    "product_url": product_url
                })

                # Optional: print to console
                # print(f"{idx}. {title} - {price} - {description} - {rating} - {review}")
                # print(f"    URL: {product_url}\n")


            # Stop after 5 pages
            if page_number >= 5:
                print("Reached 5 pages. Stopping.")
                break
            

            # Find all pagination buttons
            next_buttons = await page.query_selector_all("a._9QVEpD")

            next_button = None
            for btn in next_buttons:
                try:
                    text = await btn.inner_text()
                    if text.strip().lower() == "next":
                        next_button = btn
                        break
                except:
                    continue

            # Click on next page if found
            if next_button:
                await next_button.click()
                await page.wait_for_timeout(2000)
                page_number += 1
            else:
                print("No more pages found.")
                break

        # Save data to JSON
        with open("flipkart_products.json", "w") as f:
            json.dump(scraped_data, f, indent=4)
        print("Saved all data to flipkart_products.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_flipkart_titles_and_prices())
