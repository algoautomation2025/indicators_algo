# from flask import Flask, request, jsonify
# from datetime import datetime
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import threading
# import time
# import os

# app = Flask(__name__)

# # =========================
# # CONFIG (FROM RENDER ENV)
# # =========================
# GOOGLE_CRED_FILE = os.getenv("GOOGLE_CRED_FILE", "google_credentials.json")
# GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Trading Alerts")

# LATEST_SHEET = "Latest_Signals"
# HISTORY_SHEET = "All_Alerts"

# ALERT_EXPIRY_SECONDS = 240
# CLEANUP_INTERVAL_SECONDS = 30

# # =========================
# # DUMMY ROW (LATEST ONLY)
# # =========================
# DUMMY_TICKER = "MRF"

# DUMMY_ROW = [
#     "MRF",
#     "NSE",
#     "5",
#     "BUY",
#     "1",
#     "2000-01-01 00:00:00",
#     "2000-01-01 00:00:00"
# ]

# # =========================
# # GOOGLE AUTH
# # =========================
# scope = [
#     "https://spreadsheets.google.com/feeds",
#     "https://www.googleapis.com/auth/drive"
# ]

# creds = ServiceAccountCredentials.from_json_keyfile_name(
#     GOOGLE_CRED_FILE, scope
# )
# client = gspread.authorize(creds)

# spreadsheet = client.open(GOOGLE_SHEET_NAME)
# latest_sheet = spreadsheet.worksheet(LATEST_SHEET)
# history_sheet = spreadsheet.worksheet(HISTORY_SHEET)

# # =========================
# # TIME PARSER
# # =========================
# def parse_alert_time(raw_time):
#     try:
#         return datetime.fromisoformat(
#             raw_time.replace("Z", "+00:00")
#         ).strftime("%Y-%m-%d %H:%M:%S")
#     except:
#         return raw_time

# # =========================
# # ENSURE DUMMY ROW
# # =========================
# def ensure_dummy_row():
#     rows = latest_sheet.get_all_values()

#     if len(rows) < 2:
#         latest_sheet.insert_row(DUMMY_ROW, 2)
#         return

#     if rows[1][0] != DUMMY_TICKER:
#         latest_sheet.update("A2:G2", [DUMMY_ROW])

# # =========================
# # BACKGROUND CLEANUP
# # =========================
# def cleanup_latest_signals_forever():
#     while True:
#         try:
#             ensure_dummy_row()
#             now = datetime.now()
#             rows = latest_sheet.get_all_values()
#             rows_to_delete = []

#             for i in range(2, len(rows)):
#                 try:
#                     received_time = datetime.strptime(
#                         rows[i][6], "%Y-%m-%d %H:%M:%S"
#                     )
#                     if (now - received_time).total_seconds() > ALERT_EXPIRY_SECONDS:
#                         rows_to_delete.append(i + 1)
#                 except:
#                     continue

#             for r in reversed(rows_to_delete):
#                 latest_sheet.delete_rows(r)

#         except Exception as e:
#             print("Cleanup error:", e)

#         time.sleep(CLEANUP_INTERVAL_SECONDS)

# # =========================
# # SAVE ALERT
# # =========================
# def save_to_google_sheets(data):
#     signal_map = {"1": "BUY", "-1": "SELL"}

#     ensure_dummy_row()

#     ticker = data.get("ticker")
#     if ticker == DUMMY_TICKER:
#         return

#     row = [
#         ticker,
#         data.get("exchange"),
#         data.get("timeframe"),
#         signal_map.get(str(data.get("signal")), data.get("signal")),
#         float(data.get("price")),
#         parse_alert_time(data.get("time")),
#         datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     ]

#     # HISTORY (ALL ALERTS)
#     history_sheet.append_row(row, value_input_option="USER_ENTERED")

#     # LATEST (ONLY ONE PER TICKER)
#     rows = latest_sheet.get_all_values()
#     for i in range(2, len(rows)):
#         if rows[i][0] == ticker:
#             latest_sheet.delete_rows(i + 1)
#             break

#     latest_sheet.append_row(row, value_input_option="USER_ENTERED")

#     print(f"Saved alert for {ticker}")

# # =========================
# # WEBHOOK
# # =========================
# @app.route("/webhook", methods=["POST"])
# def webhook():
#     try:
#         data = request.get_json(force=True)
#         save_to_google_sheets(data)
#         return jsonify({"status": "success"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# # =========================
# # HEALTH CHECK
# # =========================
# @app.route("/", methods=["GET"])
# def health():
#     return "OK", 200

# # =========================
# # RUN (RENDER)
# # =========================
# if __name__ == "__main__":
#     threading.Thread(
#         target=cleanup_latest_signals_forever,
#         daemon=True
#     ).start()

#     port = int(os.environ.get("PORT", 5000))
#     print(f"Running on port {port}")
#     app.run(host="0.0.0.0", port=port)











from flask import Flask, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import threading
import time
import os

app = Flask(__name__)

# =========================
# CONFIG (FROM RENDER ENV)
# =========================
GOOGLE_CRED_FILE = os.getenv("GOOGLE_CRED_FILE", "google_credentials.json")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Trading Alerts")

LATEST_SHEET = "Latest_Signals"
HISTORY_SHEET = "All_Alerts"

ALERT_EXPIRY_SECONDS = 240
CLEANUP_INTERVAL_SECONDS = 30

# =========================
# DUMMY ROW (LATEST ONLY)
# =========================
DUMMY_TICKER = "MRF"

DUMMY_ROW = [
    "MRF",
    "NSE",
    "5",
    "BUY",
    "1",
    "2000-01-01 00:00:00",
    "2000-01-01 00:00:00"
]

# =========================
# GOOGLE AUTH
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    GOOGLE_CRED_FILE, scope
)
client = gspread.authorize(creds)

spreadsheet = client.open(GOOGLE_SHEET_NAME)
latest_sheet = spreadsheet.worksheet(LATEST_SHEET)
history_sheet = spreadsheet.worksheet(HISTORY_SHEET)

# =========================
# TIME PARSER
# =========================
def parse_alert_time(raw_time):
    try:
        return datetime.fromisoformat(
            raw_time.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return raw_time

# =========================
# ENSURE DUMMY ROW
# =========================
def ensure_dummy_row():
    rows = latest_sheet.get_all_values()

    if len(rows) < 2:
        latest_sheet.insert_row(DUMMY_ROW, 2)
        return

    if rows[1][0] != DUMMY_TICKER:
        latest_sheet.update("A2:G2", [DUMMY_ROW])

# =========================
# BACKGROUND CLEANUP
# =========================
def cleanup_latest_signals_forever():
    while True:
        try:
            ensure_dummy_row()
            now = datetime.now()
            rows = latest_sheet.get_all_values()
            rows_to_delete = []

            for i in range(2, len(rows)):
                try:
                    received_time = datetime.strptime(
                        rows[i][6], "%Y-%m-%d %H:%M:%S"
                    )
                    if (now - received_time).total_seconds() > ALERT_EXPIRY_SECONDS:
                        rows_to_delete.append(i + 1)
                except:
                    continue

            for r in reversed(rows_to_delete):
                latest_sheet.delete_rows(r)

        except Exception as e:
            print("Cleanup error:", e)

        time.sleep(CLEANUP_INTERVAL_SECONDS)

# =========================
# SAVE ALERT
# =========================
def save_to_google_sheets(data):
    signal_map = {"1": "BUY", "-1": "SELL"}

    ensure_dummy_row()

    ticker = data.get("ticker")
    if ticker == DUMMY_TICKER or not ticker:
        return

    row = [
        ticker,
        data.get("exchange"),
        data.get("timeframe"),
        signal_map.get(str(data.get("signal")), data.get("signal")),
        float(data.get("price")),
        parse_alert_time(data.get("time")),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]

    # HISTORY (ALL ALERTS)
    history_sheet.append_row(row, value_input_option="USER_ENTERED")

    # LATEST (ONLY ONE PER TICKER)
    rows = latest_sheet.get_all_values()
    for i in range(2, len(rows)):
        if rows[i][0] == ticker:
            latest_sheet.delete_rows(i + 1)
            break

    latest_sheet.append_row(row, value_input_option="USER_ENTERED")

    print(f"Saved alert for {ticker}")

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "Webhook endpoint only accepts POST requests with JSON.", 200

    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        save_to_google_sheets(data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# =========================
# RUN (RENDER)
# =========================
if __name__ == "__main__":
    threading.Thread(
        target=cleanup_latest_signals_forever,
        daemon=True
    ).start()

    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port {port}")
    app.run(host="0.0.0.0", port=port)
