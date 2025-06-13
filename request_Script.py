import requests
import pandas as pd
import time
from datetime import datetime

API_key = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUyNTg3NjcwMCwiYWFpIjoxMSwidWlkIjo3NTE3MTU4NCwiaWFkIjoiMjAyNS0wNi0xM1QwMDo0MDo0Ny4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjY5NzE0OTYsInJnbiI6InVzZTEifQ.V_Gn7B-YJWoqeRiTKOX-tbrd2Ex7gDBPgs5COhVjFmw'
board_id = '8585885825'
url = "https://api.monday.com/v2"

HEADERS = {
    "Authorization": API_key,
    "Content-Type": "application/json"
}

def count_scheduled(board_id):
    query = """
    query ($board_id: [ID!]!) {
        boards(ids: $board_id) {
        items_count
        }
    }
    """
    variables = {"board_id": [str(board_id)]}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=HEADERS)

    data = response.json()
    number_scheduled = data["data"]["boards"][0]["items_count"]
    return number_scheduled


def fetch_board_items(board_id):
    query = """
        query ($board_id: [ID!]!) {
        boards(ids: $board_id) {
            items_page(limit: 1000) {
            items {
                id
                name
                column_values {
                id
                text
                value
                }
            }
            }
        }
    }
    """
    variables = {"board_id": [str(board_id)]}

    response = requests.post(url, json={"query": query, "variables": variables}, headers=HEADERS)

    if response.status_code != 200:
        raise Exception(f"Query failed with status {response.status_code}: {response.text}")

    data = response.json()
    items = data["data"]["boards"][0]["items_page"]["items"]

    rows = []
    for item in items:
        row = {"Item ID": item["id"], "Item Name": item["name"]}
        for col in item["column_values"]:
            row[col["id"]] = col["text"]
        rows.append(row)

    return pd.DataFrame(rows)


def export_to_csv(df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f"monday_export_{timestamp}.csv", index=False)
    print(f"Exported {len(df)} items at {timestamp}")

def main():
    df = fetch_board_items(board_id)
    export_to_csv(df)

if __name__ == "__main__":
    main()
