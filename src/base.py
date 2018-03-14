import discord
import asyncio
import logging
import time

import os
import sys
sys.path.append('/usr/local/share/bkc-services')

from modules import Module as ModManager
from remote import Module as Remote
from help import Module as Help
from settings import Settings

import common

client = discord.Client()
modules = {}
advanced = {}
help = Help(True, client, modules)
mm = ModManager(True, client, modules, advanced)
t = 0
diff = 0

class logger():
	def __init__(self, func):
		self.func = func
		self.entry = ""
	def append(self, text):
		self.entry = "{}{}".format(self.entry, text)
		return self
	def nl(self):
		return self.append("\n")
	def tab(self):
		return self.append("\t\t")
	def nlt(self):
		return self.nl().tab()
	def took(self, time):
		return self.append(", Took ").append(time).append("s")
	def log(self, entry=None):
		if entry == None:
			self.func(self.entry)
			self.entry = ""
		else:
			self.func(entry)
def log(msg):
	print("[{}] {}".format(int(time.time()), msg))

l = logger(log)

@client.event
async def on_ready():
	diff = int(time.time()) - t
	l.append("Logged in with ID ").append(client.user.id).took(diff).log()
	modules["modules"] = mm
	ti = int(time.time())
	files = {}
	for filename in os.listdir('/usr/local/share/bkc-services/modules'):
		if (filename[0] != '_' and filename[0] != '.'):
			mname = os.path.splitext(filename)
			if mname[1].startswith(".py"):
				mname = mname[0]
				files[mname] = None
	sys.path.append('/usr/local/share/bkc-services/modules')
	for key in files.keys():
		mod = __import__(key)
		cls = getattr(mod, "Module")
		init = cls(common.getmodulestatus(key), client)
		l.append("Discovered module: ").append(init.__name__).log()
		if common.getmodulestatus(key):
			l.append("Initializing ").append(init.__name__).log()
		else:
			l.append(init.__name__).append(" is disabled.").log()
		if init.has_commands():
			modules[key] = init
		if init.bind_on_message():
			l.append("Binding ").append(init.__name__).append(" to on_message()").log()
			advanced[key] = init
	diff = int(time.time()) - ti
	l.append("All modules loaded").took(diff).log()
	help.set(True, client, modules)

@client.event
async def on_message(message):
	args = message.content.split(" ")
	cmd = args[0].lower()
	handled = False
	for n in modules:
		module = modules[n]
		if module.has_command(cmd):
			l.append("Command detected. '").append(cmd).append("' is registered to ").append(n).log()
		else:
			continue

		if module.permissible(cmd, common.getrank(message.author.id), message.channel.is_private):
			l.append("Creating task and inserting into loop")
			t = int(time.time())
			handled = module.receive(cmd, args, message)
			secs = int(time.time()) - t
			l.took(secs).log()
			if handled:
				l.append("Task registered successfully")
			else:
				l.append("WARNING: Task failed to register")
			l.log()
			break
		else:
			l.append("WARNING: ").append(message.author.id).append(" attempted to use a command in ")
			if message.channel.is_private:
				l.append("a chat by the name of ")
			else:
				l.append("#")
			l.append(message.channel.name).append(", but did not have the rank or permissions to do so.")

	if not handled:
		t = int(time.time())
		show_help = False
		show_modhelp = None
		args = common.strip_mentions(message.content.lower()).split(" ")
		if message.channel.is_private:
			if args[0] == "help":
				show_help = True
				if len(args) > 1:
					show_modhelp = args[1:]
		elif client.user in message.mentions:
			if args[0] == "help":
				show_help = True
				if len(args) > 1:
					show_modhelp = args[1:]
					l.append("Selected modules: ").append(", ".join(args[1:])).log()
		handled = show_help
		if handled and show_modhelp == None:
			l.append("Showing full help module")
			await help.show(message.channel)
		elif handled:
			l.append("Showing help for selected module or modules")
			await help.show_modules(message.channel, show_modhelp)
		diff = int(time.time()) - t
		if handled: l.took(diff).log()
	for n in advanced:
		await advanced[n].on_message(message)

l.append("Starting BKC Services - ").append(Settings.Version["name"]).append(" (").append(Settings.Version["code"]).append(")").log()
t = int(time.time())
remote_handler = Remote(client)
remote = client.loop.create_server(lambda: remote_handler, Settings.Remote["host"], Settings.Remote["port"])
diff = int(time.time()) - t
l.append("Remote Command Thread Started").took(diff).log()
l.append("Sending discord errors to file").log()
log = logging.getLogger('discord')
handler = logging.FileHandler(filename='/var/log/bkcs-discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
log.addHandler(handler)
t = int(time.time())
client.run("NDAyNjQxMTg1MDQwMTA1NDg1.DUyHfQ.FBIo0DYfGHc2ZZ840UgAof9XB4U")
