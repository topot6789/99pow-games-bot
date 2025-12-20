from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
import pytz
import os

app = Client("MiniGameBot", api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627", bot_token=os.getenv("BOT_TOKEN"))

daily_winners = set()
last_reset_date = datetime.now().date()
PH_TZ = pytz.timezone("Asia/Manila")


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
    return bool(
        message.forward_date
        or message.forward_from
        or message.forward_sender_name
    )

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


async def is_admin(client, message):
    # Ignore non-group
    if not message.chat:
        return False
        
    # Anonymous admin (sent as group)
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
    # Normal user admin
    if message.from_user:
        member = await client.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status.value in ("administrator", "owner")

    return False

@app.on_message(filters.command(["startdice", "stopdice", "startdarts", "stopdarts", "startslots", "stopslots", "startbasket", "stopbasket", "startfoot", "stopfoot"]) & filters.group)
async def game_control(client, message: Message):
    if not await is_admin(client, message):
        return

    cmd = message.text.lower()

    global dice_active, darts_active, slots_active, basketball_active, football_active, bowling_active

    if cmd == "/startdice":
        dice_active = True
        await message.reply("Dice game is now ACTIVE! Send 🎲 emoji  to participate")
    elif cmd == "/stopdice":
        dice_active = False
        dice_attempts.clear()
        await message.reply("Dice game stopped.❌")

    elif cmd == "/startdarts":
        darts_active = True
        await message.reply("Darts game is now ACTIVE! Send 🎯 to emoji participate")
    elif cmd == "/stopdarts":
        darts_active = False
        darts_attempts.clear()
        darts_won_first.clear()
        await message.reply("Darts game stopped.❌")

    elif cmd == "/startslots":
        slots_active = True
        await message.reply("Slot Machine is now ACTIVE! Send 🎰 to emoji participate")
    elif cmd == "/stopslots":
        slots_active = False
        slots_attempts.clear()
        await message.reply("Slot Machine stopped.❌")

    elif cmd == "/startbasket":
        basketball_active = True
        await message.reply("Basketball game is now ACTIVE! Send 🏀 emoji to participate")
    elif cmd == "/stopbasket":
        basketball_active = False
        basketball_attempts.clear()
        basketball_success.clear()
        await message.reply("Basketball game stopped.❌")

    elif cmd == "/startfoot":
        football_active = True
        await message.reply("Football game is now ACTIVE! Kick ⚽")
    elif cmd == "/stopfoot":
        football_active = False
        football_attempts.clear()
        await message.reply("Football game stopped.❌")
    
@app.on_message(filters.group)
async def detect_mini_game(client, message: Message):
    if message.sticker:
        await message.reply("This is a sticker! Please send the emoji if you wish to participate")
        return
    
    if message.dice:    
        if await is_admin(client, message):
            return

        emoji = message.dice.emoji
        value = message.dice.value          
        user = message.from_user.username or message.from_user.first_name
        user_id = message.from_user.id
        reset_daily_winners()

        if emoji.startswith("🎲") and not dice_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("🎲 Dice event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🎯") and not darts_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("🎯 Darts event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🎰") and not slots_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("🎰 Slot Machine event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🏀") and not basketball_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("🏀 Basketball event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("⚽") and not football_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("⚽ Football event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🎲"):   # Dice
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
                
            attempts = dice_attempts.get(user_id, 0)
            if attempts >= 2:
                await message.reply("You have no more dice chances this round! ❌", quote=True)
                return
                
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return

            current_attempt = attempts + 1
            dice_attempts[user_id] = current_attempt

            await message.reply(f"@{user} rolled {value} 🎲  (chance {attempts + 1}/2)")
            if value == 6:
                daily_winners.add(user_id)
                await message.reply(f"@{user} WINS 20 pesos!! (perfect 6) 🎉\n\n"
                                    f"Please send a screenshot of your P200 deposit today along with your Player ID to claim your prize.\n\n")
                if current_attempt == 1:
                    await message.reply("You won on your first try — your second chance has been removed!", quote=True)
                
                dice_attempts[user_id] = 2

        elif emoji.startswith("🎯"): # Darts
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
                
            attempts = darts_attempts.get(user_id, 0)
            if attempts >= 2:
                await message.reply("You have no chances left for this round!", quote=True)
                return
            
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return
            attempts += 1
            darts_attempts[user_id] = attempts

            score = message.dice.value

            if score == 6:  
                prize = "₱20"
                msg = f"**Congrats!!** @{user} wins {prize}** Perfect shot!\n\nPlease send a screenshot of your ₱200 deposit today along with your Player ID to claim your prize\n"
                # If won on first try → block second attempt
                daily_winners.add(user_id)
                if attempts == 1:
                    darts_attempts[user_id] = 2
                    msg += "\nYou won on your FIRST throw — second chance removed!"

            elif score > 1:  # Hit the board
                prize = "₱5"
                msg = f"Good hit! @{user} wins {prize}**\n\nPlease send a screenshot of your ₱200 deposit today along with your Player ID to claim your prize\n"
                daily_winners.add(user_id)
                if attempts == 1:
                    darts_attempts[user_id] = 2
                    msg += "\nYou won on your FIRST throw — second chance removed!"

            else:  # score == 0 → missed
                msg = f"Ouch! {user} missed the board completely!\nBetter luck on your next throw!"

            await message.reply(msg, quote=True)

        elif emoji.startswith("🎰"): # Slot Machine
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
                
            if user_id in slots_attempts:
                await message.reply("You already used your 1 slot spin this round!", quote=True)
                return
            
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return
            slots_attempts.add(user_id)
            
            s1, s2, s3 = decode_slot(value)

            status, payout = calculate_slot_payout(s1, s2, s3) 

            msg = (
                f"🎰 **Slot Machine** 🎰\n"
                f"**{status}**\n"
                f"Reward: ₱{payout}\n\n"
                "Please send a screenshot of your P500 deposit today along with your Player ID to claim your prize"
            )
            await message.reply(msg, quote=True)
            daily_winners.add(user_id)

        elif emoji.startswith("🏀"): # Basketball
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
            attempts = basketball_attempts.get(user_id, 0)
            success = basketball_success.get(user_id, 0)
            value = message.dice.value

            if attempts >= 2:
                await message.reply("You already used your 2 basketball chances this round! ❌", quote=True)
                return
            
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return
            attempts += 1
            basketball_attempts[user_id] = attempts

            made_this_shot = 1 if value >= 4 else 0
            success += made_this_shot
            basketball_success[user_id] = success

            goals_this_shot = "2 goals" if value == 5 else "1 goal" if value == 4 else "missed"
            await message.reply(f"@{user} → Shot {attempts}/2: {goals_this_shot}")


            if made_this_shot:
                await message.reply("SWISH! Made the shot!", quote=True)
            else:
                await message.reply("Airball… missed!", quote=True)

            if attempts == 1 and made_this_shot:
                daily_winners.add(user_id)
                await message.reply(
                    f"@{user} WINS ₱10 on the first shot! 🎉\n"
                    "You still have **1 more attempt**, shoot again!",
                    quote=True
                )
                return 

            if attempts == 2:
                if success == 2:
                    # Won both shots
                    daily_winners.add(user_id)
                    await message.reply(
                        f"**🤴 BASKETBALL LEGEND!!! 🤴**\n\n"
                        f"@{user} scored on **BOTH shots!**\n"
                        f"**You win ₱10 + Basketball Star title**\n\n"
                        "Please send a screenshot of your P200 deposit today along with your Player ID to claim your prize.",
                        quote=True
                    )

                elif success == 1:
                    # Won exactly one shot
                    daily_winners.add(user_id)
                    await message.reply(
                        f"Good game! @{user} made **1 out of 2 shots**\n"
                        f"**You win ₱10**\n\n"
                        "Please send a screenshot of your P200 deposit today along with your Player ID to claim your prize.",
                        quote=True
                    )

                else:
                    # Missed both shots
                    await message.reply(
                        f"Tough luck @{user}… **0/2 shots made**\n"
                        "No prize this round — better luck next time!",
                        quote=True
                    )

        elif emoji.startswith("⚽"): # Football
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return       
            
            attempts = football_attempts.get(user_id, 0)
            if attempts >= 2:
                await message.reply("You have no more football chances this round! ❌", quote=True)
                return
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return

            current_attempt = attempts + 1
            football_attempts[user_id] = current_attempt

            await message.reply(f"@{user} kicked - chance ({attempts + 1}/2)")
            if value in (4, 5, 6):
                daily_winners.add(user_id)
                await message.reply("⚽GOAL⚽\n\n"
                                    f"@{user} WINS 10 pesos!! 🎉\n\n"
                                    f"Please send a screenshot of your P200 deposit today along with your Player ID to claim your prize.\n\n")
                if current_attempt == 1:
                    await message.reply("You won on your first try — your second chance has been removed!", quote=True)
                    football_attempts[user_id] = 2
            else:
                await message.reply("Better Luck Next time!", quote=True)             

app.run()
