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
    df.to_csv(f"csv_folder/monday_export_{board_id}_{timestamp}.csv", index=False)
    csv_timestamp = f"monday_export_{board_id}_{timestamp}.csv"
    print(f"Exported {len(df)} items at {timestamp} for board # {board_id}")
    return csv_timestamp, df

def main():
    monday_boards = []
    # Boards of interest are 8585885825 which is Billing, 8586310441 which is the Census Board, 9023723118 which is Scheduling - Texas, 9023703555 is Incoming Referrals - Texas, 
    board_id = '8585885825', '8586310441', '9023723118', '9023703555', '9893934656'

    for board_id in board_id:
        df = fetch_board_items(board_id)
        current_TimeStamp, df = export_to_csv(df, board_id)
        monday_boards.append((board_id, current_TimeStamp))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.read_csv(f"csv_folder/monday_export_{'9893934656'}_{timestamp}.csv")
    rename_map = {
    "dropdown_mkv5t588": "dropdown_mkrxh1cs",
    "text_mkv56kmm": "text_mkv5d5q0",
    "location_mkv59p48": "location_mkv56zmh",
    "color_mkv5ys2r": "color_mkv5zem0",
    "color_mkv513br": "color_mknjsnb0",
    "color_mkv5902g": "color_mksm4ff9",
    "numeric_mkv5fqpc": "numeric_mknj2b0q",
    "numeric_mkv5x8dk": "numeric_mknjsfxc",
    "text_mkv5kekx": "text_mkt975v7",
    "dropdown_mkv5g7n6": "dropdown_mknjyvdf",
    "dropdown_mkv5xktq": "dropdown_mknjq1sw",
    "dropdown_mkv51mfr": "dropdown_mknj8zrs",
    "color_mkv538kn": "color_mknjqkk4",
    "color_mkv5236x": "color_mksmdve",
    "dropdown_mkv5mjdt": "dropdown_mknjhbj2",
    "color_mkv51jh2": "color_mknj2g92",
    "date_mkv5jac0": "date_mknja77s",
    "dropdown_mkv52txc": "dropdown_mknjdbxr",
    "color_mkv5w81t": "color_mknjb7ce",
    "color_mkv5k0wq": "color_mknjegtm",
    "color_mkv5tewy": "color_mknjgatn",
    "color_mkv5fbry": "color_mknj1n1b",
    "color_mkv54hpx": "color_mknj1agk",
    "color_mkv5hx99": "color_mknjzahg",
    "color_mkv5rtja": "color_mknj8ryr",
    "date_mkv5x30x": "date_mknjwhgr",
    "color_mkv5xkfn": "color_mknjp4dv"
    }

    df = df.rename(columns = rename_map)

    df.to_csv(f"csv_folder/monday_export_{'9893934656'}_{timestamp}.csv")

    return monday_boards


if __name__ == "__main__":
    main()
