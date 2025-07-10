import asyncio
import random
import string
import os
import re
import json

import discord
from discord.ext import commands
from discord import app_commands

from scripts.client import FofClient

from dotenv import load_dotenv
load_dotenv("configs/discord-secrets.env")

import yaml
config = {}

with open("configs/server-wrapper.yml", "r") as fp:
    config.update(yaml.safe_load(fp))
with open("configs/discord.yml", "r") as fp:
    config.update(yaml.safe_load(fp))

# Verification info
pending_file = config.get("verify_pending_file", "data/discord-verification/pending_verifications.json")
verified_file = config.get("verified_user_file", "data/discord-verification/verified_users.json")

def save_pending(pending):
    with open(pending_file, "w") as f:
        json.dump(pending, f)

def load_pending():
    if os.path.exists(pending_file):
        with open(pending_file, "r") as f:
            return json.load(f)
    return {}

def save_verified(verified):
    with open(verified_file, "w") as f:
        json.dump(verified, f)

def load_verified():
    if os.path.exists(verified_file):
        with open(verified_file, "r") as f:
            return json.load(f)
    return {}

pending_verifications = load_pending()
print(f"Pending users: {pending_verifications}")
verified_users = load_verified()

# Connect to FofHost
fof_host = config.get("fof_local_host", "127.0.0.1")
fof_port = config.get("fof_local_port", 9000)

fof = FofClient(host=fof_host, port=fof_port)

VERIFY_REGEX = re.compile(r'"(.+)<(\d+)><\[(.+)\]><(\w+)>" say "!verify (\w+)"')

@fof.on_event("verify_attempt")
async def handle_verification(message):
    text = message["data"].strip()
    match = VERIFY_REGEX.search(text)
    if not match:
        print("No match found in verify message.")
        return

    # Parse fields
    player_name, entity_id, steam_id, team, verify_code = match.groups()

    if verify_code in pending_verifications:
        user_id = pending_verifications.pop(verify_code)
        save_pending(pending_verifications)

        guild = bot.get_guild(GUILD_ID)
        if guild:
            member = guild.get_member(user_id)
            if member:
                role = guild.get_role(VERIFIED_ROLE_ID)
                if role:
                    await member.add_roles(role)
                    try:
                        await member.send(f"✅ You've been verified and given access!")
                    except:
                        pass
                    print(f"Verified {member.name}")

                    # Save verified users mapping
                    verified_users[steam_id] = user_id
                    save_verified(verified_users)

                else:
                    print("Verified role not found!")
            else:
                print("Member not found in guild!")
        else:
            print("Guild not found!")
    else:
        print(f"No pending verification found for code: {verify_code}")

# Discord bot

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["DISCORD_GUILD_ID"]) # as an integer
VERIFIED_ROLE_ID = int(os.environ["DISCORD_VERIFIED_ID"])  # the ID of the Verified role

intents = discord.Intents.default()
intents.members = True  # IMPORTANT: You must enable the "Server Members Intent" in your bot settings

bot = commands.Bot(command_prefix="!", intents=intents)

def generate_code(length=8):
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    while code in pending_verifications:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    return code

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

    async def on_fof_connect(client):
        await client.register_event(
            "verify_attempt",
            match_="say \"!verify "
        )

    fof.on_connect(on_fof_connect)
    if not hasattr(bot, "_fof_task") or bot._fof_task.done():
        bot._fof_task = asyncio.create_task(fof.run())
    
    synced_commands = await bot.tree.sync()
    print(f"Synced {len(synced_commands)} commands:")
    for cmd in synced_commands:
        print(f"- /{cmd.name}")
    print("Registered slash commands and event!")

@bot.event
async def on_member_join(member):
    # Send a DM with a verification code
    code = generate_code()
    pending_verifications[code] = member.id
    save_pending(pending_verifications)

    try:
        await member.send(
            f"Welcome to the server, {member.name}!\n\n"
            f"To verify your account, please join the game and type the following command in chat:\n\n"
            f"`!verify {code}`\n\n"
            f"After you do, you'll be given full access!"
        )
        print(f"Sent verification code to {member.name}")
    except Exception as e:
        print(f"Failed to send DM to {member.name}: {e}")

@app_commands.command(name="newcode", description="Generate a new verification code.")
async def newcode(interaction: discord.Interaction):
    if interaction.guild is not None:
        await interaction.response.send_message(
            "Please use this command in a private DM with me.", ephemeral=True
        )
        return

    code = generate_code()
    for k, v in {l: w for l, w in pending_verifications.items()}:
        if v == interaction.user.id:
            del pending_verifications[k]
    pending_verifications[code] = interaction.user.id
    save_pending(pending_verifications)

    try:
        await interaction.response.send_message(
            f"Here’s your new verification code!\n\n"
            f"Join the game server and type:\n"
            f"`!verify {code}`",
            ephemeral=True
        )
        print(f"Generated new code for {interaction.user.name}")
    except Exception as e:
        print(f"Failed to send new code to {interaction.user.name}: {e}")

bot.tree.add_command(newcode)

if __name__ == "__main__":
    async def main():
        await bot.start(TOKEN)
    asyncio.run(main())