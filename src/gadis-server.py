import discord
import asyncio
import logging
import time

import os
import sys
sys.path.append('/usr/local/share/gadis')

from modules import Module as ModManager
from remote import Module as Remote
from help import Module as Help
from settings import Settings

import common
import mysql

client = discord.Client()
modules = {}
advanced = {}
db = mysql.default()
help = Help(True, client, modules)
mm = ModManager(True, client, modules, advanced)
t = 0
diff = 0
logging.addLevelName(15, "EXTRA")
logging.setLoggerClass(common.LoggerExtension)
logger = logging.getLogger("GADIS")
logger.setLevel(1)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] %(message)s')
ch = logging.StreamHandler(sys.stdout)
fh = logging.FileHandler(filename='/var/log/gadis/debug.log', encoding='utf-8', mode='w')
ch.setLevel(logging.INFO)
fh.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)

@client.event
async def on_ready():
	diff = int(time.time()) - t
	logger.info("Logged in with ID {} ({}s)".format(client.user.id, diff))
	logger.info("Ensuring brand...")
	await client.edit_profile(None, username="Gadis")
	modules["modules"] = mm
	logger.info("Loading modules...")
	ti = int(time.time())
	files = {}
	for filename in os.listdir('/usr/local/share/gadis/modules'):
		if (filename[0] != '_' and filename[0] != '.'):
			mname = os.path.splitext(filename)
			if mname[1].startswith(".py"):
				mname = mname[0]
				files[mname] = None
	sys.path.append('/usr/local/share/gadis/modules')
	for key in files.keys():
		mod = __import__(key)
		cls = getattr(mod, "Module")
		init = cls(common.getmodulestatus(db, key), db, client)
		if common.getmodulestatus(db, key):
			logger.info("{} is enabled.".format(init.__name__))
		else:
			logger.info("{} is disabled.".format(init.__name__))
		if init.has_commands():
			modules[key] = init
		if init.bind_on_message():
			logger.extra("Binding {}".format(init.__name__))
			advanced[key] = init
	diff = int(time.time()) - ti
	logger.info("No more modules. ({}s)".format(diff))
	help.set(True, client, modules)

@client.event
async def on_message(message):
	args = message.content.split(" ")
	cmd = args[0].lower()
	handled = False
	for n in modules:
		module = modules[n]
		if not module.has_command(cmd): continue

		if module.permissible(cmd, common.getrank(db, message.author.id), message.channel.is_private):
			t = int(time.time())
			handled = module.receive(cmd, args, message)
			break
		else:
			s = "{} attempted to use a command in ".format(message.author.id)
			if message.channel.is_private:
				s = "{}a chat by the name of ".format(s)
			else:
				s = "{}#".format(s)
			logger.warn("{}{}, but did not have the rank or permissions to do so.".format(s, message.channel.name))

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
					logger.debug("Selected modules: {}".format(", ".join(args[1:])))
		handled = show_help
		s = "Displayed help for {} module{} ("
		if handled and show_modhelp == None:
			s = s.format("all", "s")
			await help.show(message.channel)
		elif handled:
			s.format("selected", " or modules")
			await help.show_modules(message.channel, show_modhelp)
		diff = int(time.time()) - t
		if handled: logger.info("{}{}s)".format(s, diff))
	for n in advanced:
		await advanced[n].on_message(message)

logger.info("Starting Gadis - {} ({})".format(Settings.Version["name"], Settings.Version["code"]))
t = int(time.time())
remote_handler = Remote(db, client)
remote = client.loop.create_server(lambda: remote_handler, Settings.Remote["host"], Settings.Remote["port"])
client.loop.create_task(remote)
diff = int(time.time()) - t
logger.info("Remote Command Thread Started ({}s)".format(diff))
logger.info("Sending discord errors to file")
log = logging.getLogger('discord')
handler = logging.FileHandler(filename='/var/log/gadis/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
log.addHandler(handler)
t = int(time.time())
client.run(Settings.DiscordToken)
