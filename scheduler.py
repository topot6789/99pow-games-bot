import asyncio
from datetime import datetime, time as dtime
import pytz
from pyrogram import Client
from pyrogram.types import ChatPermissions

# ───────────────── CONFIG ─────────────────

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = os.getenv("BOT_TOKEN")

TARGET_CHAT_ID = -1003539357826
PH_TZ = pytz.timezone("Asia/Manila")

LOCK_TIME = dtime(hour=23, minute=13)
UNLOCK_TIME = dtime(hour=23, minute=14)

LOCKED_PERMISSIONS = ChatPermissions(
    can_send_messages=False
)

UNLOCKED_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True
)

CHECK_INTERVAL = 60  # seconds

def get_desired_state(now: dtime) -> str:
    """
    Returns 'locked' or 'unlocked'
    Handles midnight crossover correctly
    """
    if LOCK_TIME > UNLOCK_TIME:
        # crosses midnight
        return "locked" if (now >= LOCK_TIME or now < UNLOCK_TIME) else "unlocked"
    else:
        return "locked" if LOCK_TIME <= now < UNLOCK_TIME else "unlocked"


async def permission_watcher(app: Client):
    last_state = None

    # small startup delay
    await asyncio.sleep(3)

    while True:
        now = datetime.now(PH_TZ).time()
        desired_state = get_desired_state(now)

        if desired_state != last_state:
            if desired_state == "locked":
                await app.set_chat_permissions(
                    TARGET_CHAT_ID,
                    LOCKED_PERMISSIONS
                )
                print("[SCHEDULER] Group LOCKED")
            else:
                await app.set_chat_permissions(
                    TARGET_CHAT_ID,
                    UNLOCKED_PERMISSIONS
                )
                print("[SCHEDULER] Group UNLOCKED")

            last_state = desired_state

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    app = Client(
        "permission_scheduler",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )

    await app.start()
    print("[SCHEDULER] Started")

    await permission_watcher(app)


if __name__ == "__main__":
    asyncio.run(main())
