import discord
import asyncio

import sys
sys.path.append('/usr/local/share/bkc-services')

from insultreply import Module as InsultReply
from accounts import Module as Accounts
from antispam import Module as AntiSpam
from utility import Module as Utility
from remote import Module as Remote
from ranks import Module as Ranks
from help import Module as Help
from fun import Module as Fun

from settings import Settings

import common

client = discord.Client()
modules = []
advanced = []
help = Help(True, client, modules)

@client.event
async def on_ready():
	fun = Fun(True, client)
	modules.append(Accounts(True, client))
	modules.append(Utility(True, client))
	modules.append(Ranks(True, client))
	modules.append(fun)
	advanced.append(fun)
	advanced.append(AntiSpam(True, client))
	advanced.append(InsultReply(True, client))
	help.set(True, client, modules)

@client.event
async def on_message(message):
	args = message.content.split(" ")
	cmd = args[0].lower()
	handled = False
	for module in modules:
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
	for module in advanced:
		await module.on_message(message)

remote_handler = Remote(client)
remote = client.loop.create_server(lambda: remote_handler, Settings.RemoteHost, Settings.RemotePort)
client.run("NDAyNjQxMTg1MDQwMTA1NDg1.DUyHfQ.FBIo0DYfGHc2ZZ840UgAof9XB4U")
