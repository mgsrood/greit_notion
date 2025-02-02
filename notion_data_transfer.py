import requests
import json
import os
from google.cloud import bigquery
import pandas as pd
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Base URL
url = os.getenv("NOTION_API_URL")

# Authorization
access_token = os.getenv("NOTION_API_TOKEN")
headers = {
    "Authorization": "Bearer " + access_token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
database_id = os.getenv("NOTION_DATABASE_ID")

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
    task = props["Taak"]["rich_text"][0]["text"]["content"]
    date = props["Datum"]["date"]["start"]
    hours = props["Uren"]["number"]

    data_list.append({"ID": id, "Client": client, "Project": project, "Task": task, "Date": date, "Hours": hours})

# Create a DataFrame
df = pd.DataFrame(data_list)

# Extract the IDs
if not df.empty:
    list = df['ID']
    existing_id_list = list.astype(int)
else:
    existing_id_list = []

# Define Get Data From BigQuery
def get_data_from_bigquery(project_id, dataset_id, table_id):
    
    # Make a BigQuery client
    client = bigquery.Client(project=project_id)

    # Build the reference to the dataset
    table_ref = client.dataset(dataset_id).table(table_id)

    # Get the table
    table = client.get_table(table_ref)

    # Load the data into a DataFrame
    df = client.list_rows(table).to_dataframe()

    return df

# Get the BigQuery keys
gc_keys = os.getenv("GREIT_GOOGLE_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gc_keys

# BigQuery information
project_id = os.getenv("UREN_REGISTRATIE_PROJECT_ID")
dataset_id = os.getenv("UREN_REGISTRATIE_DATASET_ID")
table_id = os.getenv("UREN_REGISTRATIE_TABLE_ID")
full_table_id = f'{project_id}.{dataset_id}.{table_id}'

# Get the BigQuery data
dataframe = get_data_from_bigquery(project_id, dataset_id, table_id)

# Filter out existing IDs
if not df.empty:
    df_to_upload = dataframe[~dataframe['ID'].isin(existing_id_list)]
else:
    df_to_upload = dataframe

# Writing endpoint for Notion
endpoint = f"https://api.notion.com/v1/pages/"

# Iterate over DataFrame rows
if df_to_upload.empty:
    print("Geen nieuwe gegevens om te uploaden naar Notion.")
else:
    for index, row in df_to_upload.iterrows():
        # Details of the new rows
        new_row_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "ID": {"title": [{"text": {"content": str(row['ID'])}}]},
                "Datum": {"date": {"start": row['Datum'].strftime("%Y-%m-%d")}},
                "Uren": {"number": row['Uren']},
                "Klant": {"rich_text": [{"text": {"content": row['Klant']}}]} if not pd.isna(row['Klant']) else {"rich_text": [{"text": {"content": "Algemeen"}}]},
                "Project": {"rich_text": [{"text": {"content": row['Project']}}]},
                "Taak": {"rich_text": [{"text": {"content": row['Taak']}}]}
            }
        }
        
        # Send a POST-request to write new data
        response = requests.post(endpoint, headers=headers, json=new_row_data)

        # Check the status
        if response.status_code == 200:
            print(f"Rij {index + 1} succesvol toegevoegd aan de Notion Database.")
        else:
            print(f"Fout bij het toevoegen van rij {index + 1}:", response.text)
