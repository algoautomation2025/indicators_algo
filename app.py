from flask import Flask, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import threading
import time
import os
import requests
import json
from threading import Lock

app = Flask(__name__)

# =========================
# CONFIG
# =========================
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Trading Alerts")

LATEST_SHEET = "Latest_Signals"
HISTORY_SHEET = "All_Alerts"

ALERT_EXPIRY_SECONDS = 240
CLEANUP_INTERVAL_SECONDS = 60
KEEP_ALIVE_INTERVAL = 300

# =========================
# THREAD LOCK (CRITICAL)
# =========================
gsheet_lock = Lock()

# =========================
# DUMMY ROW (LATEST ONLY)
# =========================
DUMMY_TICKER = "MRF"
DUMMY_ROW = [
    "MRF",
    "NSE",
    "5",
    "BUY",
    1,
    "2000-01-01 00:00:00",
    "2000-01-01 00:00:00"
]

# =========================
# GOOGLE AUTH (RENDER SAFE)
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

google_creds_json = os.getenv("GOOGLE_CRED_JSON")
if not google_creds_json:
    raise RuntimeError("GOOGLE_CRED_JSON env var not set")

creds_dict = json.loads(google_creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
spreadsheet = client.open(GOOGLE_SHEET_NAME)
latest_sheet = spreadsheet.worksheet(LATEST_SHEET)
history_sheet = spreadsheet.worksheet(HISTORY_SHEET)

# =========================
# TIME PARSER (UTC)
# =========================
def parse_alert_time(raw_time):
    try:
        if raw_time is None:
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if str(raw_time).isdigit():
            ts = int(raw_time) / 1000
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

        return datetime.fromisoformat(
            str(raw_time).replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        print("Time parse error:", e)
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# =========================
# ENSURE DUMMY ROW
# =========================
def ensure_dummy_row():
    with gsheet_lock:
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
            with gsheet_lock:
                ensure_dummy_row()
                now = datetime.utcnow()
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
# KEEP ALIVE (RENDER)
# =========================
def self_ping_forever():
    url = os.getenv("SELF_URL")
    if not url:
        return

    while True:
        try:
            requests.get(url, timeout=5)
        except Exception as e:
            print("Self-ping error:", e)
        time.sleep(KEEP_ALIVE_INTERVAL)

# =========================
# SAVE ALERT
# =========================
def save_to_google_sheets(data):
    required = ["ticker", "exchange", "timeframe", "signal", "price", "time"]
    for k in required:
        if k not in data:
            raise ValueError(f"Missing field: {k}")

    ticker = str(data["ticker"]).strip().upper()
    if ticker == DUMMY_TICKER:
        return

    raw_signal = str(data["signal"]).upper()
    if raw_signal in ["BUY", "1"]:
        signal = "BUY"
    elif raw_signal in ["SELL", "-1"]:
        signal = "SELL"
    else:
        raise ValueError(f"Invalid signal: {raw_signal}")

    price = float(data["price"])

    row = [
        ticker,
        data["exchange"],
        data["timeframe"],
        signal,
        price,
        parse_alert_time(data["time"]),
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ]

    with gsheet_lock:
        ensure_dummy_row()

        history_sheet.append_row(
            row, value_input_option="USER_ENTERED"
        )

        rows = latest_sheet.get_all_values()
        for i in range(2, len(rows)):
            if rows[i][0] == ticker:
                latest_sheet.delete_rows(i + 1)
                break

        latest_sheet.append_row(
            row, value_input_option="USER_ENTERED"
        )

    print(f"Saved alert for {ticker}")

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        save_to_google_sheets(data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"error": str(e)}), 500

# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# =========================
# RUN
# =========================
if __name__ == "__main__":
    threading.Thread(
        target=cleanup_latest_signals_forever, daemon=True
    ).start()

    threading.Thread(
        target=self_ping_forever, daemon=True
    ).start()

    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port {port}")
    app.run(host="0.0.0.0", port=port)