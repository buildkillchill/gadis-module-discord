import discord
import asyncio
import time

import os
import sys
sys.path.append('/usr/local/share/bkc-services')

from modules import Module as ModManager
from remote import Module as Remote
from help import Module as Help
from settings import Settings

import common
import mysql

client = discord.Client()
modules = {}
advanced = {}
help = Help(True, client, modules)
mm = ModManager(True, client, modules)

class logger():
	def __init__(self, func):
		self.func = func
		self.entry = ""
	def append(self, text):
		self.entry = "{}{}".format(self.entry, text)
		return self
	def nl(self):
		self.entry = "{}\n".format(self.entry)
		return self
	def tab(self):
		self.entry = "{}\t\t".format(self.entry)
		return self
	def log(self, entry=None):
		if entry == None:
			self.func(self.entry)
			self.entry = ""
		else:
			self.func(entry)
def log(msg):
	print("[{}] {}".format(int(time.time()), msg))
	mysql.default().run("INSERT INTO `log` (`message`) VALUES (%s)", [msg])

l = logger(log)

@client.event
async def on_ready():
	l.append("Logged in with ID ").append(client.user.id).log()
	modules["modules"] = mm
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
		l.append("Discovered module: ").append(init.__name__).nl().tab().append("Status: ")
		if common.getmodulestatus(key):
			l.append("Enabled")
		else:
			l.append("Disabled")
		l.nl().tab().append("Commands: ")
		if init.has_commands():
			l.append("Yes")
			modules[key] = init
		else:
			l.append("No")
		l.nl().tab().append("Bound: ")
		if init.bind_on_message():
			l.append("Yes")
			advanced[key] = init
		else:
			l.append("No")
		l.log()
	help.set(True, client, modules)

@client.event
async def on_message(message):
	args = message.content.split(" ")
	cmd = args[0].lower()
	handled = False
	for n in modules:
		module = modules[n]
		if module.has_command(cmd) and module.permissible(cmd, common.getrank(message.author.id), message.channel.is_private):
			l.append("'").append(cmd).append("' is handled by the ").append(n).append(" module.").nl().tab()
			t = int(time.time())
			handled = module.receive(cmd, args, message)
			secs = int(time.time()) - t
			l.append("Took ").append(secs).append("s").nl().tab().append("Status: ")
			if handled:
				l.append("Success")
			else:
				l.append("Failure")
			l.log()
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

l.append("Starting BKC Services").nl().tab()
l.append("Version:  3.02").nl().tab()
l.append("Codename: DynaFly").log()
remote_handler = Remote(client)
remote = client.loop.create_server(lambda: remote_handler, Settings.RemoteHost, Settings.RemotePort)
l.log(entry="Remote Command Thread Started")
client.run("NDAyNjQxMTg1MDQwMTA1NDg1.DUyHfQ.FBIo0DYfGHc2ZZ840UgAof9XB4U")
