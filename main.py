import discord
import asyncio
import socket
import os
import aiohttp
from aiohttp import web

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)

async def get_server_status():
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(os.environ['TCP_HOST'], int(os.environ['TCP_PORT'])), 
            timeout=5
        )
        writer.close()
        await writer.wait_closed()
        return 'UP'
    except (ConnectionRefusedError, asyncio.TimeoutError):
        return 'DOWN'

async def check_tcp_server():
    if os.path.exists('status.txt'):
        with open('status.txt', 'r') as f:
            previous_status = f.read().strip()
    else:
        previous_status = None
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((os.environ['TCP_HOST'], int(os.environ['TCP_PORT'])))
            s.close()
            status = 'UP'
        except:
            status = 'DOWN'
        if status != previous_status:
            embed = discord.Embed(title='Dragon Nest Server Status', color=0xFF0000)
            if status == 'UP':
                embed.color = 0x00FF00
                embed.description = ':green_circle: The Server is [**Online**!](https://sea.dragonnest.com/news/notice/all)'
                embed.set_image(url="https://media.discordapp.net/attachments/520389517996326917/1009018983544012820/unknown.png")
                message = f'<@&{os.environ["PING_ROLE_ID"]}> The server is **Online**!'
            else:
                embed.description = ':red_circle: The Server is [**Offline**!](https://sea.dragonnest.com/news/notice/all)'
                embed.set_image(url="https://media.discordapp.net/attachments/520389517996326917/1009061896118358096/unknown.png")
                message = f'<@&{os.environ["PING_ROLE_ID"]}> The server is **Offline**!'
            message_channel = client.get_channel(int(os.environ['DISCORD_CHANNEL_ID']))
            if os.path.exists('embed_message_id.txt'):
                with open('embed_message_id.txt', 'r') as f:
                    embed_message_id = f.read().strip()
            else:
                embed_message_id = None
            if embed_message_id is not None:
                try:
                    previous_embed_message = await message_channel.fetch_message(int(embed_message_id))
                    await previous_embed_message.delete()
                except discord.NotFound:
                    pass
            message_embed = await message_channel.send(embed=embed)
            with open('embed_message_id.txt', 'w') as f:
                f.write(str(message_embed.id))
            ping_message = await message_channel.send(message)
            await asyncio.sleep(10)
            await ping_message.delete()
            previous_status = status
            with open('status.txt', 'w') as f:
                f.write(previous_status)
        await asyncio.sleep(30)

async def hello(request):
    return web.Response(text="Hello, world!")

async def start_webapp():
    app = web.Application()
    app.add_routes([web.get('/', hello)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, os.environ['WEBAPP_HOST'], int(os.environ['WEBAPP_PORT']))
    await site.start()

async def start_services():
    await asyncio.gather(check_tcp_server(), start_webapp())

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    client.loop.create_task(start_services())

client.run(os.environ['DISCORD_BOT_TOKEN'])
