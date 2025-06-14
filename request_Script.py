import requests
import pandas as pd
import time
from datetime import datetime
import json

API_key = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUyNTg3NjcwMCwiYWFpIjoxMSwidWlkIjo3NTE3MTU4NCwiaWFkIjoiMjAyNS0wNi0xM1QwMDo0MDo0Ny4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjY5NzE0OTYsInJnbiI6InVzZTEifQ.V_Gn7B-YJWoqeRiTKOX-tbrd2Ex7gDBPgs5COhVjFmw'
url = "https://api.monday.com/v2"

HEADERS = {
    "Authorization": API_key,
    "Content-Type": "application/json"
}


def fetch_board_items(board_id):
    query = """
    query ($board_id: [ID!]!, $cursor: String) {
      boards(ids: $board_id) {
        items_page(limit: 500, cursor: $cursor) {
          cursor
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

    all_items = []
    cursor = None

    while True:
        variables = {
            "board_id": [str(board_id)],
            "cursor": cursor
        }

        response = requests.post(url, json={"query": query, "variables": variables}, headers=HEADERS)

        if response.status_code != 200:
            raise Exception(f"Query failed with status {response.status_code}: {response.text}")

        data = response.json()
        board_data = data["data"]["boards"][0]

        if not board_data or "items_page" not in board_data:
            raise Exception("No items_page data found in response.")

        page = board_data["items_page"]
        items = page["items"]
        all_items.extend(items)

        cursor = page.get("cursor")
        if not cursor:
            break
        

    rows = []
    for item in all_items:
        row = {"Item ID": item["id"], "Item Name": item["name"]}
        for col in item["column_values"]:
            row[col["id"]] = col["text"]
        rows.append(row)

    return pd.DataFrame(rows)


def export_to_csv(df, board_id):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f"monday_export_{board_id}_{timestamp}.csv", index=False)
    csv_timestamp = f"monday_export_{board_id}_{timestamp}.csv"
    print(f"Exported {len(df)} items at {timestamp} for board # {board_id}")
    return csv_timestamp, df

def main():
    monday_boards = []
    # Boards of interest are 8585885825 which is Billing, 8586310441 which is the Census Board, 9023723118 which is Scheduling - Texas, 9023703555 is Incoming Referrals - Texas, 
    board_id = '8585885825', '8586310441', '9023723118', '9023703555'

    for board_id in board_id:
        df = fetch_board_items(board_id)
        current_TimeStamp, df = export_to_csv(df, board_id)
        monday_boards.append((board_id, current_TimeStamp))

    return monday_boards


if __name__ == "__main__":
    main()
