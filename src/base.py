import discord
import asyncio

import os
import sys
sys.path.append('/usr/local/share/bkc-services')

from remote import Module as Remote
from help import Module as Help
from settings import Settings

import common

client = discord.Client()
modules = {}
advanced = {}
help = Help(True, client, modules)

@client.event
async def on_ready():
	files = {}
	for filename in os.listdir('/usr/local/share/bkc-services/modules'):
		if (filename[0] != '_' and filename[0] != '.'):
			mname = filename[:-4]
			files[mname] = None
	sys.path.append('/usr/local/share/bkc-services/modules')
	for key in files.keys():
		mod = __import__(key)
		cls = getattr(mod, "Module")
		init = cls(common.getmodulestatus(key), client)
		print("Discovered module: {}".format(init.__name__))
		print("\tEnabled: {}".format(common.getmodulestatus(key)))
		if init.has_commands():
			modules[key] = init
		if init.bind_on_message():
			advanced[key] = init
	help.set(True, client, modules)

@client.event
async def on_message(message):
	args = message.content.split(" ")
	cmd = args[0].lower()
	handled = False
	for n in modules:
		module = modules[n]
		if module.has_command(cmd) and module.permissible(cmd, common.getrank(message.author.id), message.channel.is_private):
			handled = module.receive(cmd, args, message)
			break
	if not handled:
		if message.channel.is_private and message.content.lower() == "help":
			handled = True
			await help.show(message.channel)
		elif not message.channel.is_private:
			if (message.content.lower().startswith("help") or message.content.lower().endswith("help")) and client.user in message.mentions:
				handled = True
				await help.show(message.channel)
	for n in advanced:
		await advanced[n].on_message(message)

remote_handler = Remote(client)
remote = client.loop.create_server(lambda: remote_handler, Settings.RemoteHost, Settings.RemotePort)
client.run("NDAyNjQxMTg1MDQwMTA1NDg1.DUyHfQ.FBIo0DYfGHc2ZZ840UgAof9XB4U")
