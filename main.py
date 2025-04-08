import discord
from discord.ext import commands, tasks
from pydactyl import PterodactylClient
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load credentials from .env:

PANEL_URL = os.getenv("PANEL_URL")
API_KEY = os.getenv("API_KEY") # Pterodactyl User API Key.
SERVER_ID = os.getenv("SERVER_ID")
NODE = os.getenv("NODE") # Just the node name for your reference.
TOKEN = os.getenv("TOKEN")

api = PterodactylClient(url=PANEL_URL, api_key=API_KEY)

class ServerControlButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="start_button")
    async def start_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer() 
        try:
            api.client.servers.send_power_action(SERVER_ID, 'start')
            await interaction.followup.send("Server started successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to start server. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Restart", style=discord.ButtonStyle.gray, custom_id="restart_button")
    async def restart_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer() 
        try:
            api.client.servers.send_power_action(SERVER_ID, 'restart')
            await interaction.followup.send("Server restarted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to restart server. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, custom_id="stop_button")
    async def stop_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  
        try:
            api.client.servers.send_power_action(SERVER_ID, 'stop')
            await interaction.followup.send("Server stopped successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to stop server. Error: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Channel ID where the embed should be posted
    channel_id = 0000000000000000000  # Replace with your channel ID
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(title="Pterodactyl server", description="Use the buttons below to control the server.", color=discord.Color.red())
        embed.add_field(name="Server ID:", value=SERVER_ID, inline=False)
        embed.add_field(name="Node:", value=NODE, inline=False)
        embed.add_field(name="Server Status:", value="Checking...", inline=False)
        view = ServerControlButtons()
        message = await channel.send(embed=embed, view=view)
        
        bot.message_id = message.id
        bot.channel_id = channel.id
        check_server_status.start()
        update_footer.start()
    else:
        print(f"Channel with ID {channel_id} not found.")

@tasks.loop(seconds=30) # adjust the loop according to your liking.
async def check_server_status():
    channel = bot.get_channel(bot.channel_id)
    if channel:
        try:
            server = api.client.servers.get_server_utilization(SERVER_ID)
            state = server['current_state']
            status = "Online" if state == "running" else "Offline"
        except Exception as e:
            status = str(e)

        message = await channel.fetch_message(bot.message_id)
        
        new_embed = discord.Embed(title="Pterodactyl server", description="Use the buttons below to control the server.", color=discord.Color.red())
        new_embed.add_field(name="Server ID:", value=SERVER_ID, inline=False)
        new_embed.add_field(name="Node:", value=NODE, inline=False)
        new_embed.add_field(name="Server Status:", value=status, inline=False)

        if message.embeds:
            old_embed = message.embeds[0]
            if old_embed.footer:
                new_embed.set_footer(text=old_embed.footer.text)

        await message.edit(embed=new_embed)

@tasks.loop(seconds=30) # adjust the loop according to your liking.
async def update_footer():
    channel = bot.get_channel(bot.channel_id)
    if channel:
        try:
            message = await channel.fetch_message(bot.message_id)
            embed = message.embeds[0]

            now = discord.utils.utcnow()
            next_ping_time = now + datetime.timedelta(seconds=30 - (now.second % 30))
            remaining_seconds = (next_ping_time - now).seconds

            embed.set_footer(text=f"Next ping in {remaining_seconds} s")

            await message.edit(embed=embed)
        except Exception as e:
            status = str(e)
            new_embed = discord.Embed(title="Pterodactyl server", description="Use the buttons below to control the server.", color=discord.Color.red())
            new_embed.add_field(name="Server ID:", value=SERVER_ID, inline=False)
            new_embed.add_field(name="Node:", value=NODE, inline=False)
            new_embed.add_field(name="Server Status:", value=status, inline=False)
            await message.edit(embed=new_embed)
            
bot.run(TOKEN)
