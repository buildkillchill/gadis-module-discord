import discord
import asyncio

import sys
sys.path.append('/usr/local/share/bkc-services')

from help import Module as Help
from settings import Settings

import common

client = discord.Client()
modules = []
advanced = []
help = Help(True, client, modules)

@client.event
async def on_ready():
	files = {}
	for filename in os.listdir('/usr/local/share/bkc-services/modules')
		if (filename[0] != '_' and filename[0] != '.'):
			files[filename.rstrip('.pyc')] = None
	sys.path.append('/usr/local/share/bkc-services/modules')
	for key in files.keys():
		mod = __import__(key)
		cls = getattr(mod, "Module")
		init = cls(False, client)
		if init.has_commands():
			modules.append(init)
		if init.bind_on_message():
			advanced.append(init)
#	fun = Fun(common.modulestatus(Fun.__name__), client)
#	modules.append(Accounts(common.modulestatus(Accounts.__name__), client))
#	modules.append(Utility(common.modulestatus(Utility.__name__), client))
#	modules.append(Ranks(common.modulestatus(Ranks.__name__), client))
#	modules.append(fun)
#	advanced.append(fun)
#	advanced.append(AntiSpam(common.modulestatus(AntiSpam.__name__), client))
#	advanced.append(InsultReply(common.modulestatus(InsultReply.__name__), client))
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
