#!/usr/bin/env python3

import discord
import os
import logging
import yaml

with open("config.yml", 'r') as stream:
    config = yaml.safe_load(stream)

GUILDS = config['guilds']
TOKEN = config['token']

activeChannels = []

client = discord.Client()

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

# TODO: Cleanup `activeChannels` by checking to see if the channel is deleted

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    logging.debug(message)
    # If we're the bot, just return
    if message.author == client.user:
        return

    # Check to see if the user is in a role that can moderate
    guild = message.guild
    guildConfig = GUILDS[guild.id]

    if message.content.startswith(guildConfig['command']):
        # Check to see if we're in a configured moderation channel
        if message.channel.id not in guildConfig['modChannels']:
            logging.info(f"Got message in {message.channel.name} ({message.channel.id}) which is not configured")
            return

        # Check to see if the user has a configured role
        roleIDs=set()
        for role in message.author.roles:
            roleIDs.add(role.id)

        if len(roleIDs.intersection(guildConfig['roles'])) == 0:
            logging.info(f"Got message from {message.author.name} without valid role ({set(message.author.roles)})")
            return

        if len(message.mentions) == 0 or len(message.mentions) > 1:
            await message.channel.send(f"<@{message.author.id}> you need to mention the single user you are looking to talk with.")
            logging.info(f"Got message with zero, or to many mentions {message.mentions}")
            return

        moderatedUser = message.mentions[0]

        # Create the channel using the users name
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            moderatedUser: discord.PermissionOverwrite(read_messages=True)
        }

        for roleId in guildConfig['roles']:
            roleSearch = discord.utils.get(guild.roles, id=roleId)
            overwrites[roleSearch] = discord.PermissionOverwrite(read_messages=True)

        if guildConfig is not None:
            category = client.get_channel(guildConfig['category'])
        else:
            category = None

        botChannel = await guild.create_text_channel(moderatedUser.name, overwrites=overwrites, category=category)
        activeChannels.append(botChannel.id)

        await botChannel.send(f"Welcome <@{moderatedUser.id}> to your moderation room, this room is logged.")

client.run(TOKEN)
