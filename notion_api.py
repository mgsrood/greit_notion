import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Base url
url = os.getenv("NOTION_API_URL")

# Authorization
access_token = os.getenv("NOTION_API_TOKEN")
database_id = os.getenv("NOTION_DATABASE_ID")
headers = {
    "Authorization": "Bearer " + access_token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Data extraction function
def get_pages(num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()
    
    import json
    with open('db.json', 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]

    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

# Run function and create an empty data list
pages = get_pages()
data_list = []

# Iterate over the data rows
for page in pages:
    page_id = page["id"]
    props = page["properties"]
    id = props["ID"]["title"][0]["text"]["content"]
    client = props["Klant"]["rich_text"][0]["text"]["content"]
    project = props["Project"]["rich_text"][0]["text"]["content"]
    areas = props['Areas']["rich_text"][0]["text"]["content"]
    task = props["Taak"]["rich_text"][0]["text"]["content"]
    date = props["Datum"]["date"]["start"]
    hours = props["Uren"]["number"]

    data_list.append({"ID": id, "Client": client, "Project": project, "Task": task, "Date": date, "Hours": hours})

# Create a DataFrame
df = pd.DataFrame(data_list)

print(df)