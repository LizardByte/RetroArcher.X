#!/usr/bin/env python
import discord
import os

from dotenv import load_dotenv

load_dotenv()

# load the changelog
with open('changelog.md', 'r') as f:
    lines = f.readlines()

found_version = False
title = ''
selftext = ''

# parse the changelog
for line in lines:
    if line.startswith('##'):
        if not found_version:
            title = 'Released %s' % (line.replace('##', '').strip())
            version = line.replace('##', '').strip().split(' ', 1)[0]
            selftext = '**Changelog:**'
            found_version = True
        else:
            break
    else:
        if found_version:
            if line.startswith('*'):  # this is a category, let's underline it
                selftext += '\n__%s__' % (line[1:].strip())
            else:
                selftext += '\n%s' % (line.strip())

# add the download link
if title != '':
    try:
        embedUrl = 'https://github.com/%s/releases/%s' % (os.environ['GITHUB_REPOSITORY'], version)
        selftext += '\n[Download](%s)' % (embedUrl)
    except KeyError:
        embedUrl = 'https://github.com/RetroArcher'

# constants
client_secret = os.environ['DISCORD_CLIENT_SECRET']
client = discord.Client(intents=discord.Intents.all())

channel_id = int(os.environ['DISCORD_CHANNEL_ID'])

botName = 'RetroArcher'
botUrl = 'https://github.com/RetroArcher'
iconUrl = 'https://raw.githubusercontent.com/RetroArcher/RetroArcher.branding/main/logos/RetroArcher-white-256x256.png'


# on ready
@client.event
async def on_ready():  # Called when internal cache is loaded
    channel = client.get_channel(channel_id)  # Gets channel from internal cache

    embed = discord.Embed(title=title, url=embedUrl,
                          description=selftext,
                          color=discord.Color.orange())
    embed.set_author(name=botName, url=botUrl,
                          icon_url=iconUrl)

    await channel.send(embed=embed)
    await client.close()


# Login the bot
client.run(client_secret)
