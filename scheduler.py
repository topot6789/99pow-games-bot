import time
import requests
from datetime import datetime, time as dtime
import pytz

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = -1003539357826

PH_TZ = pytz.timezone("Asia/Manila")

LOCK_TIME = dtime(hour=0, minute=30)
UNLOCK_TIME = dtime(hour=0, minute=31)

def get_desired_state(now):
    if LOCK_TIME > UNLOCK_TIME:
        return "locked" if (now >= LOCK_TIME or now < UNLOCK_TIME) else "unlocked"
    return "locked" if LOCK_TIME <= now < UNLOCK_TIME else "unlocked"

def set_permissions(can_send: bool):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatPermissions"
    payload = {
        "chat_id": CHAT_ID,
        "permissions": {
            "can_send_messages": can_send,
            "can_send_media_messages": can_send,
            "can_send_other_messages": can_send
        }
    }
    requests.post(url, json=payload, timeout=10)

last_state = None

while True:
    now = datetime.now(PH_TZ).time()
    state = get_desired_state(now)

    if state != last_state:
        set_permissions(state == "unlocked")
        print("[SCHEDULER]", state)
        last_state = state

    time.sleep(60)
