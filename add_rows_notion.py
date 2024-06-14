import requests
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Base URL
url = os.getenv("NOTION_API_URL")

# Authorization
access_token = os.getenv("NOTION_API_TOKEN")
database_id = os.getenv("NOTION_DATABASE_ID")
headers = {
    "Authorization": "Bearer " + access_token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Define endpoint URL for adding rows to the database
add_row_url = f"{url}/pages"

# Sample data to add to the database
new_row_data = {
    "parent": { "database_id": database_id },
    "properties": {
        "ID": { "title": [{ "text": { "content": "449079" }}]},
        "Datum": { "date": { "start": "2024-01-01" }},
        "Uren": { "number": 0.2789 },
        "Klant": { "rich_text": [{ "text": { "content": "Aard'g" }}]},
        "Project": { "rich_text": [{ "text": { "content": "Algemeen" }}]},
        "Taak": { "rich_text": [{ "text": { "content": "Klantenservice" }}]}
    }
}

# Make a POST request to add a new row to the database
response = requests.post(add_row_url, headers=headers, json=new_row_data)

# Check the status of the request
if response.status_code == 200:
    print("Row successfully added to the Notion database!")
else:
    print("An error occurred while adding the row to the Notion database.")
    print(response.text)
