from aiogram.client.default import DefaultBotProperties
import asyncio
import logging
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions,
)
from aiogram import Router
bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
command_router = Router()
game_router = Router()

logging.basicConfig(level=logging.INFO)
daily_winners = set()
last_reset_date = datetime.now().date()
PH_TZ = pytz.timezone("Asia/Manila")

BLOCKED_KEYWORDS = [
    "customer service",
    "customerservice",
    "support",
    " cs ",
    "agent",
    "admin",
    "official",
    "support",
    "help desk",
    "helpdesk",
    "99bon",
    "99pow"
]

accepted_users = set()

dice_active = False
darts_active = False
slots_active = False
basketball_active = False
football_active = False

dice_attempts = {}
basketball_attempts={}
darts_attempts={}
slots_attempts=set()
football_attempts={}
basketball_success = {}
basketball_winners = set()
darts_won_first = set()
result=''
SLOT_SYMBOLS = ["🍒", "🍋", "7️⃣", "BAR"]

GAME_EMOJI_MAP = {
    "Dice": "🎲",
    "Basketball": "🏀",
    "Slots": "🎰",
    "Football": "⚽",
    "Darts":"🎯"
}

def looks_like_impersonation(user):
    name_parts = [
        user.first_name or "",
        user.last_name or "",
    ]

    full_name = " ".join(name_parts).lower()

    return any(keyword in full_name for keyword in BLOCKED_KEYWORDS)

async def set_group_permissions(chat_id, permissions):
    try:
        await bot.set_chat_permissions(chat_id, permissions)
    except Exception as e:
        print(f"[ERROR] Failed to set permissions: {e}")

def get_active_game_emojis():
    active = []
    if dice_active:
        active.append(GAME_EMOJI_MAP["Dice"])
    if basketball_active:
        active.append(GAME_EMOJI_MAP["Basketball"])
    if slots_active:
        active.append(GAME_EMOJI_MAP["Slots"])
    if darts_active:
        active.append(GAME_EMOJI_MAP["Darts"])
    if football_active:
        active.append(GAME_EMOJI_MAP["Football"])
    return active

def is_forwarded(message: Message) -> bool:
    return bool(message.forward_origin)

def reset_daily_winners():
    global daily_winners, last_reset_date
    now_ph = datetime.now(PH_TZ)
    today_ph = now_ph.date()

    if today_ph != last_reset_date:
        daily_winners.clear()
        last_reset_date = today_ph

def decode_slot(value: int):
    n = value - 1
    s1 = SLOT_SYMBOLS[n % 4]
    s2 = SLOT_SYMBOLS[(n // 4) % 4]
    s3 = SLOT_SYMBOLS[(n // 16) % 4]
    return s1, s2, s3


def calculate_slot_payout(s1, s2, s3):
    if s1 == s2 == s3:
        return "JACKPOT!!!", 777
    if s1 == s2 or s1 == s3 or s2 == s3:
        return "Nice! You hit 2 of a kind!", 77
    return "Well Done!", 7


async def is_admin(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return False

    member = await bot.get_chat_member(
        message.chat.id,
        message.from_user.id
    )
    return member.status in ("administrator", "creator")

def is_command(message, names):
    if not message.text:
        return False

    text = message.text.strip()
    if not text.startswith("/"):
        return False

    cmd = text.split()[0][1:]      
    cmd = cmd.split("@")[0].lower()  
    return cmd in names

@command_router.message()
async def game_control(message: Message):
    # === filters.group ===
    if message.chat.type not in ("group", "supergroup"):
        return

    COMMANDS = {
        "sdice", "stdice",
        "sdarts", "stdarts",
        "sslots", "stslots",
        "sbasket", "stbasket",
        "sfoot", "stfoot",
    }

    # === filters.command([...]) ===
    if not is_command(message, COMMANDS):
        print("BYE BYE!")
        return

    if not await is_admin(message):
        try:
            await message.delete()
        except Exception:
            pass

        await bot.send_message(
            message.chat.id,
            "🎮Please send the proper emoji of the game that is currently active🎮"
        )
        return

    cmd = message.text.split()[0].lower()

    global dice_active, darts_active, slots_active
    global basketball_active, football_active

    if cmd == "/sdice":
        dice_active = True
        await message.answer("Dice game is now ACTIVE! Send 🎲 emoji to participate")
        await bot.send_dice(message.chat.id, emoji="🎲")

    elif cmd == "/stdice":
        dice_active = False
        dice_attempts.clear()
        await message.answer("Dice game stopped.❌")

    elif cmd == "/sdarts":
        darts_active = True
        await message.answer("Darts game is now ACTIVE! Send 🎯 emoji to participate")
        await bot.send_dice(message.chat.id, emoji="🎯")

    elif cmd == "/stdarts":
        darts_active = False
        darts_attempts.clear()
        darts_won_first.clear()
        await message.answer("Darts game stopped.❌")

    elif cmd == "/sslots":
        slots_active = True
        await message.answer("Slot Machine is now ACTIVE! Send 🎰 emoji to participate")
        await bot.send_dice(message.chat.id, emoji="🎰")

    elif cmd == "/stslots":
        slots_active = False
        slots_attempts.clear()
        await message.answer("Slot Machine stopped.❌")

    elif cmd == "/sbasket":
        basketball_active = True
        await message.answer("Basketball game is now ACTIVE! Send 🏀 emoji to participate")
        await bot.send_dice(message.chat.id, emoji="🏀")

    elif cmd == "/stbasket":
        basketball_active = False
        basketball_attempts.clear()
        basketball_success.clear()
        await message.answer("Basketball game stopped.❌")

    elif cmd == "/sfoot":
        football_active = True
        await message.answer("Football game is now ACTIVE! Kick ⚽")
        await bot.send_dice(message.chat.id, emoji="⚽")

    elif cmd == "/stfoot":
        football_active = False
        football_attempts.clear()
        await message.answer("Football game stopped.❌")
    print("IDK")
    return

@dp.message()
async def block_private_messages(message: Message):
    if message.chat.type != "private":
        return

    await message.forward(7855698973)
    await message.answer(
        "This bot is actually a dead-end for private messages.\n\n"
        "Please submit the screenshot of your deposit along with your player ID "
        "if you wanna claim your prize, **ONLY** in the 99POW-OFFICIAL Group."
    )


@game_router.message()
async def detect_mini_game(message: Message):
    if message.text and message.text.startswith("/"):
        return

    if message.content_type != "dice":
        return


    emoji = message.dice.emoji
    value = message.dice.value          
    user = message.from_user.username or message.from_user.first_name
    user_id = message.from_user.id
    reset_daily_winners()

    if emoji.startswith("🎲") and not dice_active:
        active_games = get_active_game_emojis()
        if active_games:
            await message.answer(
                "🚫 **This game is not active.**\n\n"
                "🎮 Active games you can play:\n"
                + "\n".join(f"• {g}" for g in active_games)
                + "\n\n👉 Send the emoji of the game you want to play."
            )
        else:
            await message.answer("🎲 Dice event is currently **not active**. ❌")
        return

    if emoji.startswith("🎯") and not darts_active:
        active_games = get_active_game_emojis()
        if active_games:
            await message.answer(
                "🚫 **This game is not active.**\n\n"
                "🎮 Active games you can play:\n"
                + "\n".join(f"• {g}" for g in active_games)
                + "\n\n👉 Send the emoji of the game you want to play."
            )
        else:
            await message.answer("🎯 Darts event is currently **not active**. ❌")
        return

    if emoji.startswith("🎰") and not slots_active:
        active_games = get_active_game_emojis()
        if active_games:
            await message.answer(
                "🚫 **This game is not active.**\n\n"
                "🎮 Active games you can play:\n"
                + "\n".join(f"• {g}" for g in active_games)
                + "\n\n👉 Send the emoji of the game you want to play."
            )
        else:
            await message.answer("🎰 Slot Machine event is currently **not active**. ❌")
        return

    if emoji.startswith("🏀") and not basketball_active:
        active_games = get_active_game_emojis()
        if active_games:
            await message.answer(
                "🚫 **This game is not active.**\n\n"
                "🎮 Active games you can play:\n"
                + "\n".join(f"• {g}" for g in active_games)
                + "\n\n👉 Send the emoji of the game you want to play."
            )
        else:
            await message.answer("🏀 Basketball event is currently **not active**. ❌")
        return

    if emoji.startswith("⚽") and not football_active:
        active_games = get_active_game_emojis()
        if active_games:
            await message.answer(
                "🚫 **This game is not active.**\n\n"
                "🎮 Active games you can play:\n"
                + "\n".join(f"• {g}" for g in active_games)
                + "\n\n👉 Send the emoji of the game you want to play."
            )
        else:
            await message.answer("⚽ Football event is currently **not active**. ❌")
        return

    if emoji.startswith("🎲"):   # Dice
        if is_forwarded(message):
            await message.answer("🚫 Forwarding an emoji is not allowed!")
            return
            
        attempts = dice_attempts.get(user_id, 0)
        if attempts >= 2:
            await message.answer("You have no more dice chances this round! ❌")
            return
            
        if user_id in daily_winners:
            await message.answer("🚫 You have already won in another game today! Come back tomorrow 😊")
            return

        current_attempt = attempts + 1
        dice_attempts[user_id] = current_attempt

        await message.answer(f"@{user} rolled {value} 🎲  (chance {attempts + 1}/2)")
        if value == 6:
            daily_winners.add(user_id)
            await message.answer(f"@{user} WINS 20 pesos!! (perfect 6) 🎉\n\n"
                                f"Please send a screenshot of your P200 deposit made today along with your Player ID to claim your prize.\n\n"
                                 "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted.")
            if current_attempt == 1:
                await message.answer("You won on your first try — your second chance has been removed!")
            
            dice_attempts[user_id] = 2

    elif emoji.startswith("🎯"): # Darts
        if is_forwarded(message):
            await message.answer("🚫 Forwarding an emoji is not allowed!")
            return
            
        attempts = darts_attempts.get(user_id, 0)
        if attempts >= 2:
            await message.answer("You have no chances left for this round!")
            return
        
        if user_id in daily_winners:
            await message.answer("🚫 You have already won in another game today! Come back tomorrow 😊")
            return
        attempts += 1
        darts_attempts[user_id] = attempts

        score = message.dice.value

        if score == 6:  
            prize = "₱20"
            msg = (f"**Congrats!!** @{user} wins {prize}** Perfect shot!\n\nPlease send a screenshot of your ₱200 deposit made today along with your Player ID to claim your prize\n\n"
                   "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted.")
            # If won on first try → block second attempt
            daily_winners.add(user_id)
            if attempts == 1:
                darts_attempts[user_id] = 2
                msg += "\nYou won on your FIRST throw — second chance removed!"

        elif score > 1:  # Hit the board
            prize = "₱5"
            msg = (f"Good hit! @{user} wins {prize}**\n\nPlease send a screenshot of your ₱200 deposit made today along with your Player ID to claim your prize\n\n"
                   "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted.")
            daily_winners.add(user_id)
            if attempts == 1:
                darts_attempts[user_id] = 2
                msg += "\nYou won on your FIRST throw — second chance removed!"

        else:  # score == 0 → missed
            msg = f"Ouch! {user} missed the board completely!\nBetter luck on your next throw!"

        await message.answer(msg)

    elif emoji.startswith("🎰"): # Slot Machine
        if is_forwarded(message):
            await message.answer("🚫 Forwarding an emoji is not allowed!")
            return
            
        if user_id in slots_attempts:
            await message.answer("You already used your 1 slot spin this round!")
            return
        
        if user_id in daily_winners:
            await message.answer("🚫 You have already won in another game today! Come back tomorrow 😊")
            return
        slots_attempts.add(user_id)
        
        s1, s2, s3 = decode_slot(value)

        status, payout = calculate_slot_payout(s1, s2, s3) 

        msg = (
            f"🎰 **Slot Machine** 🎰\n"
            f"**{status}**\n"
            f"Reward: ₱{payout}\n\n"
            "Please send a screenshot of your P500 deposit made today along with your Player ID to claim your prize\n\n"
            "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted."
        )
        await message.answer(msg)
        daily_winners.add(user_id)

    elif emoji.startswith("🏀"): # Basketball
        if is_forwarded(message):
            await message.answer("🚫 Forwarding an emoji is not allowed!")
            return
        attempts = basketball_attempts.get(user_id, 0)
        success = basketball_success.get(user_id, 0)
        value = message.dice.value

        if attempts >= 2:
            await message.answer("You already used your 2 basketball chances this round! ❌")
            return
        
        if user_id in daily_winners:
            await message.answer("🚫 You have already won in another game today! Come back tomorrow 😊")
            return
        attempts += 1
        basketball_attempts[user_id] = attempts

        made_this_shot = 1 if value >= 4 else 0
        success += made_this_shot
        basketball_success[user_id] = success

        goals_this_shot = "2 goals" if value == 5 else "1 goal" if value == 4 else "missed"
        await message.answer(f"@{user} → Shot {attempts}/2: {goals_this_shot}")


        if made_this_shot:
            await message.answer("SWISH! Made the shot!")
        else:
            await message.answer("Airball… missed!")

        if attempts == 1 and made_this_shot:
            daily_winners.add(user_id)
            await message.answer(
                f"@{user} WINS ₱10 on the first shot! 🎉\n"
                "You still have **1 more attempt**, shoot again!",
                
            )
            return 

        if attempts == 2:
            if success == 2:
                # Won both shots
                daily_winners.add(user_id)
                await message.answer(
                    f"**🤴 BASKETBALL LEGEND!!! 🤴**\n\n"
                    f"@{user} scored on **BOTH shots!**\n"
                    f"**You win ₱10 + Basketball Star title**\n\n"
                    "Please send a screenshot of your P200 deposit made today along with your Player ID to claim your prize.\n\n"
                    "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted.",
                    
                )

            elif success == 1:
                # Won exactly one shot
                daily_winners.add(user_id)
                await message.answer(
                    f"Good game! @{user} made **1 out of 2 shots**\n"
                    f"**You win ₱10**\n\n"
                    "Please send a screenshot of your P200 deposit made today along with your Player ID to claim your prize.\n\n"
                    "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted.",
                    
                )

            else:
                # Missed both shots
                await message.answer(
                    f"Tough luck @{user}… **0/2 shots made**\n"
                    "No prize this round — better luck next time!",
                    
                )

    elif emoji.startswith("⚽"): # Football
        if is_forwarded(message):
            await message.answer("🚫 Forwarding an emoji is not allowed!")
            return       
        
        attempts = football_attempts.get(user_id, 0)
        if attempts >= 2:
            await message.answer("You have no more football chances this round! ❌")
            return
        if user_id in daily_winners:
            await message.answer("🚫 You have already won in another game today! Come back tomorrow 😊")
            return

        current_attempt = attempts + 1
        football_attempts[user_id] = current_attempt

        await message.answer(f"@{user} kicked - chance ({attempts + 1}/2)")
        if value in (4, 5, 6):
            daily_winners.add(user_id)
            await message.answer("⚽GOAL⚽\n\n"
                                f"@{user} WINS 10 pesos!! 🎉\n\n"
                                f"Please send a screenshot of your P200 deposit made today along with your Player ID to claim your prize.\n\n"
                                 "<b>NOTE</b> The deposit must be made before playing the game. Deposits made after gameplay will not be accepted.")
            if current_attempt == 1:
                await message.answer("You won on your first try — your second chance has been removed!")
                football_attempts[user_id] = 2
        else:
            await message.answer("Better Luck Next time!") 

@dp.message()
async def greet_new_member(message: Message):
    if not message.new_chat_members:
        return
    
    for user in message.new_chat_members:
        if user.is_bot:
            continue

        chat_id = message.chat.id
        user_id = user.id

        if looks_like_impersonation(user):
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
            return

        # Restrict user
        await bot.restrict_chat_member(
            chat_id, user_id,
            ChatPermissions(can_send_messages=False)
        )
 
        keyboard = [[InlineKeyboardButton("✅ Accept Rules", callback_data=f"accept_{user_id}")]]
        await bot.send_message(
            chat_id,
            f"""
        👋 Welcome @{user.username}!

‼️PAALALA‼️

1️⃣Kung may problema sa inyong mga account ay   makipag ugnayan lamang sa aming; <a href="https://chat.wellytalk.com/MDE5YTM4NGQtNGNkYi03MWVlLWJjOGEtZWI4ZjQ4OTRiNTExfDM0ZjY3OTEzYjM4NWYwMGM0NDNjNzVlZjA1NGYzODNhYmQ3ZmY4NDE2ZDQ0NmFjOTgxMzAxM2Y1MGM5YWVlNmM=">Customer Service</a>.  


👉Kung may mensahi matanggap at nagsasabing sila ay:  “CUSTOMER SERVICE ”, “SUPPORT ”, “AGENT”, O “ADMIN" ay  Wag agad maniwala:

                                   🙅🏻‍♂️TANDAAN👎

👉HINDI kami kailanman  mag mensahi o tumawag  para mag-alok ng deposit, withdrawal, bonus, promo code, at  payment link.

2️⃣ PROTEKTAHAN ANG SARILI AT ANG INYONG PONDO 

Huwag magtiwala sa mga private message, link, o nino man na Manghinge ng  bayad mula sa kahit sino.

Maging  responsable na  protektahan ang iyong account at pondo sa lahat ng oras.

3️⃣ PROTEKTAHAN ANG INYONG ACCOUNT 
Huwag kailanman ibahagi ang iyong password, OTP, o detalye ng pagbabayad sa kahit sino.

4️⃣LAYUNIN NG GROUP
Ang group na ito ay para lamang sa mga laro, events, at announcements.
Para sa mga may problema sa account, makipag-ugnayan lamang sa <a href="https://chat.wellytalk.com/MDE5YTM4NGQtNGNkYi03MWVlLWJjOGEtZWI4ZjQ4OTRiNTExfDM0ZjY3OTEzYjM4NWYwMGM0NDNjNzVlZjA1NGYzODNhYmQ3ZmY4NDE2ZDQ0NmFjOTgxMzAxM2Y1MGM5YWVlNmM=">Customer Service</a> gamit ang opisyal  link.

5️⃣ IGALANG ANG KOMUNIDAD 
Walang spam, pang-aabuso, o istorbo sa grupo.

👉 I-click ang Accept Rules para magpatuloy
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


@dp.callback_query()
async def handle_callback(callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    # Ensure only the intended user can click
    if not data or not data.endswith(str(user_id)):
        await callback_query.answer("❌ This is not for you!", show_alert=True)
        return

    chat_id = callback_query.message.chat.id

    # Get current group permissions
    chat = await bot.get_chat(chat_id)
    group_perms = chat.permissions

    # Restore permissions to group defaults
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=group_perms
    )

    # Edit the rules message
    await callback_query.message.edit_text(
        f"✅ @{callback_query.from_user.username} accepted the rules. Welcome!"
    )

    accepted_users.add(user_id)

    await callback_query.answer(
        "You are now allowed to chat!",
        show_alert=True
    )

dp.include_router(command_router)
dp.include_router(game_router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
