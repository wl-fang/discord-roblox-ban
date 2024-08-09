import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
from datetime import datetime
from typing import Optional
import json

TOKEN = '12345abc'  # Replace with your actual bot token
ROBLOX_API_KEY = '12345abc' # Replace with your Roblox Cloud API Key - Enable universe read/write access
WEB_API_URL = 'https://games.roblox.com/v1/games?universeIds=id' # Replace id with your game's universeid
PATCH_API_URL = 'https://apis.roblox.com/cloud/v2/universes/id/user-restrictions/' # Replace id with your game's universeid

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='pls ', intents=intents)

def is_admin(interaction: discord.Interaction) -> bool:
    roles = [role.name for role in interaction.user.roles]
    print(f"User: {interaction.user.name}, Roles: {roles}")
    return 'Admin' in roles or 'dev' in roles or 'Trial Mod' in roles

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    change_channel_name.start()
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@app_commands.check(is_admin)
@bot.tree.command(name='activeusers', description='How many people are playing?')
async def activeusers(interaction: discord.Interaction):
    """Fetch and display active users from a Roblox place."""
    try:
        response = requests.get(WEB_API_URL)
        if response.status_code == 200:
            data = response.json()
            active_users = data['data'][0].get('playing', 'No data available')
            visits = data['data'][0].get('visits', 'No data available')
            await interaction.response.send_message(f'Current active users: {active_users}\nTotal Visits: {visits}')
            channel = bot.get_channel(1264425714330107946)
            channel2 = bot.get_channel(1264468786304651264)
            if channel and channel2:
                await channel.edit(name=f'Players Online: {active_users}')
                await channel2.edit(name=f'Total Visits: {visits}')
        else:
            await interaction.response.send_message('Failed to fetch active users data.')
    except Exception as e:
        await interaction.response.send_message(f'Error: {str(e)}')

async def activeusers_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.MissingRole):
        await interaction.response.send_message("You don't have the permissions to use this command.")

@app_commands.check(is_admin)
@bot.tree.command(name='ingameban', description='Ban a player in-game (can only be run by admins).')
async def ingameban(interaction: discord.Interaction, username: str, reason: str = None):

    duration = None

    url = 'https://users.roblox.com/v1/usernames/users'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    payload = {
        'usernames': [username],
        'excludeBannedUsers': False
    }

    theresponse = requests.post(url,json = payload,headers=headers)
    data = theresponse.json()

    theUserId = data['data'][0]['id']

    headers = {
        'x-api-key': ROBLOX_API_KEY,  # Replace with your API key if needed
    }

    payload = {}

    if duration is not None:
        duration_seconds = int(86400 * duration)
        payload = {
            'gameJoinRestriction':
                {
                    'active': True,
                    'duration': f"{duration_seconds}",
                    'excludeAltAccounts': False,
                    'inherited': True,
                    'privateReason': "Banned Player",
                    'displayReason': f'Banned for {duration} days on {datetime.today()}.'
                }
        }
    else:
        payload = {
            'gameJoinRestriction':
                {
                    'active': True,
                    'duration': duration,
                    'excludeAltAccounts': False,
                    'inherited': True,
                    'privateReason': "Banned Player",
                    'displayReason': "Banned"
                }
        }

    if reason is None:
        reason = "No reason given"

    try:
        response = requests.patch(f'{PATCH_API_URL}{theUserId}', json=payload, headers=headers)
        if response.status_code == 200:
            if duration == None:
                channel = bot.get_channel(1267292694573748255)
                await interaction.response.send_message(f'{username} has been banned indefinitely. Moderator Reason: {reason}')
                await channel.send(f'{username} was banned by {interaction.user.name}. Moderator Reason: {reason}')
            else:
                channel = bot.get_channel(1267292694573748255)
                await interaction.response.send_message(f'{username} has been banned for {duration} days.')
                await channel.send(f'{username} was banned by {interaction.user.name} for {duration} days.')
        else:
            await interaction.response.send_message(f'Failed to ban player. Status code: {response.status_code}')
    except Exception as e:
        await interaction.response.send_message(f'Error: {str(e)}')

@app_commands.check(is_admin)
@bot.tree.command(name='ingameunban', description='Unban a player in-game (can only be run by admins).')
async def ingameunban(interaction: discord.Interaction, username: str, reason: str = None):
    url = 'https://users.roblox.com/v1/usernames/users'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    # Define the payload
    payload = {
        'usernames': [username],
        'excludeBannedUsers': False
    }

    theresponse = requests.post(url, json=payload, headers=headers)
    data = theresponse.json()

    theUserId = data['data'][0]['id']

    headers = {
        'x-api-key': ROBLOX_API_KEY,  # Replace with your API key if needed
    }
    payload = {
        'gameJoinRestriction':
            {
                'active': False
            }
    }

    if reason is None:
        reason = "No reason given"

    try:
        response = requests.patch(f'{PATCH_API_URL}{theUserId}', json=payload, headers=headers)
        if response.status_code == 200:
            channel = bot.get_channel(1267292827855884288)
            await interaction.response.send_message(f'{username} has been unbanned. Moderation Reason: {reason}')
            await channel.send(f'{username} was unbanned by {interaction.user.name}. Moderation Reason: {reason}')
        else:
            await interaction.response.send_message(f'Failed to unban player. Status code: {response.status_code}')
    except Exception as e:
        await interaction.response.send_message(f'Error: {str(e)}')

async def ingameban_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.MissingRole):
        await interaction.response.send_message("You don't have the permissions to use this command.")

@bot.event
async def on_application_command_error(interaction: discord.Interaction, error: Exception):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("You don't have permission to use this command.")
    else:
        await interaction.response.send_message(f'An error occurred: {str(error)}')


@tasks.loop(minutes=6)  # Set the loop to run every x time
async def change_channel_name():
    channel = bot.get_channel(1264425714330107946)
    channel2 = bot.get_channel(1264468786304651264)
    if channel and channel2:
        try:
            response = requests.get(WEB_API_URL)
            if response.status_code == 200:
                data = response.json()
                active_users = data['data'][0].get('playing', 'No data.')
                visits = data['data'][0].get('visits', 'No data available')
                new_name = f"Players Online: {active_users}"
                await channel.edit(name=new_name)
                await channel2.edit(name=f'Total Visits: {visits}')
            else:
                await print('Failed to fetch place data.')
        except Exception as e:
            await print(f'Error: {str(e)}')
    else:
        print(f'Channel(s) not found.')

bot.run(TOKEN)
