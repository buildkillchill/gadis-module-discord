import re
import time
import discord
import asyncio
import datetime

import common

from settings import Settings

class DefCon():
	def __init__(self, client=None, level=4):
		self.client = client
		self.level = level
	def speed(self):
		  if self.level == 1: return dict(count=1, delay=3600)
		elif self.level == 2: return dict(count=1, delay=30  )
		elif self.level == 3: return dict(count=2, delay=5   )
		elif self.level == 4: return dict(count=3, delay=1   )
		elif self.level == 5: return dict(count=5, delay=1   )
	def identical(self):
		  if self.level == 1: return 0
		elif self.level == 2: return 2
		elif self.level == 3: return 3
		elif self.level == 4: return 5
		elif self.level == 5: return 8
	def drag(self):
		  if self.level == 1: return dict(characters=r'((\S\s?)\2{2,})',  emoji=r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{1,})' )
		elif self.level == 2: return dict(characters=r'((\S\s?)\2{3,})',  emoji=r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{3,})' )
		elif self.level == 3: return dict(characters=r'((\S\s?)\2{4,})',  emoji=r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{4,})' )
		elif self.level == 4: return dict(characters=r'((\S\s?)\2{9,})',  emoji=r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{9,})' )
		elif self.level == 5: return dict(characters=r'((\S\s?)\2{49,})', emoji=r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{19,})')
	def setlevel(self, args, pmsg):
		if self.client == None: return
		level = args[1]
		if level == "1" or level == "2" or level == "3" or level == "4" or level == "5":
			self.client.send_message(pmsg.channel, "@everyone Server Anti-Spam is now in DEFCON{}".format(level))
			self.level = level
		else:
			self.client.send_message(pmsg.channel, "{}, please... For everyone's sake, learn the syntax for the security commands before you try to use them.".format(pmsg.author.mention))

class SpamTables():
	def __init__(self, db, userID, defcon=DefCon()):
		self.id = userID
		self.db = db
		self.defcon = defcon
		self.db.run("INSERT IGNORE INTO `antispam` (`id`, `timestamp`) VALUES ({}, {})".format(self.id, int(time.time())))
	def column(self, name):
		value = self.db.query("SELECT `{}` FROM `antispam` WHERE `id`={}".format(name, self.id))
		return value[0][0]
	def increment(self, name):
		self.db.run("UPDATE `antispam` SET `{0}`=`{0}`+1 WHERE `id`={1}".format(name, self.id))
	def zero(self, name):
		self.db.run("UPDATE `antispam` SET `{}`=0 WHERE `id`={}".format(name, self.id))
	def mute_until(self, time):
		self.db.run("UPDATE `antispam` SET `mute_until`={} WHERE `id`={}".format(time, self.id))
	def count(self):
		return self.column("violations")
	def identical(self):
		return self.column("identical")
	def fastmsg(self):
		return self.column("fast")
	def message(self):
		return self.column("message")
	def time(self):
		return int(self.column("timestamp"))
	def muted_until(self):
		return int(self.column("mute_until"))
	def spammed(self):
		self.increment("violations")
	def messaged(self, contents):
		if int(time.time()) - self.time() < self.defcon.fast().delay:
			self.increment("fast")
		else:
			self.zero("fast")

		self.db.run("UPDATE `antispam` SET `timestamp`='{}' WHERE `id`={}".format(int(time.time()), self.id))
		if contents.encode('utf-8', "ignore") == self.message() and int(time.time()) - self.time() < 300:
			self.increment("identical")
		else:
			self.db.run("UPDATE `antispam` SET `message`=%s WHERE `id`={}".format(self.id), [contents.encode('utf-8', "ignore")])
			self.zero("identical")

class Module(common.BaseModule):
	__name__ = "Anti-Spam"
	__version__ = "2.12"
	def __init__(self, enabled, db, client=None):
		common.BaseModule.__init__(self, enabled, db, client, True)
		self.server = common.getserver(self.client)
		self.silenced = discord.utils.get(self.server.roles, id=str(Settings.Roles["silent"]))
		self.defcon = DefCon(client)
		self.client.loop.create_task(self.unsilence())
		self.addcmd("asignore", self.ignore, "Adds or removes people from the anti-spam ignore list.", rank=Settings.OwnerRank, usage="asignore on|off @mention1 .. @mentionN")
		self.addcmd("ignorechan", self.ignore_channel, "Adds or removes channels from the anti-spam ignore list.", rank=Settings.OwnerRank, usage="ignorechan on|off #channel1 .. #channelN")
		self.addcmd("!defcon", self.defcon.setlevel, "Sets the spam DEFCON level.", rank=Settings.OwnerRank, usage="!defcon {1-5}")
	async def unsilence(self):
		while True:
			for person in self.server.members:
				if self.silenced not in person.roles: continue
				user = SpamTables(self.db, person.id)
				if int(user.muted_until()) <= int(time.time()):
					await self.client.remove_roles(person, self.silenced)
			dt = datetime.datetime.now()
			await asyncio.sleep(60-dt.second)
	async def silence(self, person, t):
		await self.client.add_roles(person, self.silenced)
		user = SpamTables(self.db, person.id)
		user.mute_until(int(time.time()) + (t * 60))
	def run_punishment(self, person, time):
		self.client.loop.create_task(self.silence(person, time))
	async def punish(self, message):
		author = message.author
		user = SpamTables(self.db, author.id)
		await self.client.delete_message(message)
		if user.count() == 0:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed.".format(author.mention))
		elif user.count() < 5:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for 5 minutes.".format(author.mention))
			self.run_punishment(author, 5)
		elif user.count() < 15:
			time = (user.count() - 4) * 5
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for {} minutes.".format(author.mention, time))
			self.run_punishment(author, time)
		elif user.count() < 25:
			time = user.count() * 12.5
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for {} minutes.".format(author.mention, time))
			self.run_punishment(author, time)
		elif user.count() >= 25:
			await self.client.add_roles(author, self.silenced)
			msg = await self.client.send_message(message.channel, "{} will be kicked for spamming in 5s".format(author.mention))
			time = 5
			while time > 0:
				time = time - 1
				await asyncio.sleep(1)
				await self.client.edit_message(msg, "{} will be kicked for spamming 30+ times in {}s".format(author.mention, time))
			await self.client.edit_message(msg, "Kicking {}...".format(author.mention, time))
			await self.client.kick(author)
			await self.client.edit_message(msg, "Kicked {} right in the nut sack. Let 'em brew in pain for a bit. :wink:".format(author.mention, time))
		user.spammed()
	async def match_del(self, pattern, message):
		match = re.search(pattern, message.content.lower())
		if match:
			await self.punish(message)
	async def ignore(self, args, pmsg):
		nargs = common.strip_mentions(" ".join(args[1:])).split(" ")
		if len(nargs) > 1:
			await self.send(pmsg.channel, "Uh... that's a few too many arguments mate.")
			return
		if nargs[0] == "" or nargs[0] == "on":
			val = "TRUE"
			ret = True
		elif nargs[0] == "off":
			val = "FALSE"
			ret = False
		else:
			await self.send(pmsg.channel, "Uh... I only support on or off.")
			return
		for person in pmsg.mentions:
			sql = "INSERT INTO `antispam` (`id`,`ignore`) VALUES ({0},{1}) ON DUPLICATE KEY UPDATE `ignore`={1}".format(person.id, val)
			self.db.run(sql)
		await self.send(pmsg.channel, "Anti-Spam scanning is now set to **{}** messages from the mentioned people.".format("IGNORE" if ret else "SCAN"))
	async def ignore_channel(self, args, pmsg):
		for channel in pmsg.channel_mentions:
			val = "FALSE"
			cos = "ON"
			if args[1] == "on":
				cos = "OFF"
				sql = "INSERT IGNORE INTO `antispam_ignore` (`id`) VALUES ({})".format(channel.id)
			elif args[1] == "off":
				sql = "DELETE FROM `antispam_ignore` WHERE `id`={}".format(channel.id)
			self.db.run(sql)
		await self.send(pmsg.channel, "Anti-Spam has been turned **{}** for mentioned channels.".format(cos))
	async def on_message(self, message):
		if not await common.BaseModule.on_message(self, message): return
		if message.author == self.client.user or message.channel.is_private or len(self.db.query("SELECT * FROM `antispam` WHERE `id`={} AND `ignore`=TRUE".format(message.author.id))) > 0: return
		if len(self.db.query("SELECT * FROM `antispam_ignore` WHERE `id`={}".format(message.channel.id))) > 0:
			if len(message.mentions) > 0: await self.client.delete_message(message)
			else: return
		await self.match_del(self.defcon.drag().characters, message)
		await self.match_del(self.defcon.drag().emojis    , message)
		user = SpamTables(self.db, message.author.id, self.defcon)
		user.messaged(message.content)
		if user.fastmsg() > self.defcon.fast().count or user.identical() > self.defcon.identical() or user.fastmsg() > self.defcon.fast().delay:
			await self.punish(message)
