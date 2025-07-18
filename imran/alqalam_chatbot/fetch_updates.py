import requests
from bs4 import BeautifulSoup
import json

def scrape_updates(url, category):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.select("article")[:5]  # Get latest 5 posts
    updates = []

    for article in articles:
        title = article.find("h2", class_="entry-title")
        summary = article.find("div", class_="td-excerpt")

        updates.append({
            "category": category,
            "title": title.text.strip() if title else "No title",
            "summary": summary.text.strip() if summary else "No summary",
            "link": title.find("a")["href"] if title else ""
        })

    return updates

if __name__ == "__main__":
    news = scrape_updates("https://auk.edu.ng/category/news/", "News")
    announcements = scrape_updates("https://auk.edu.ng/category/announcement/", "Announcement")

    all_updates = news + announcements

    with open("latest_updates.json", "w", encoding="utf-8") as f:
        json.dump(all_updates, f, indent=4, ensure_ascii=False)

    print("✅ Latest updates saved to latest_updates.json")
