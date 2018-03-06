import re
import time
import discord
import asyncio

import common
import mysql

from settings import Settings

class SpamTables():
	def __init__(self, userID):
		self.id = userID
		self.db = mysql.default()
		self.db.run("INSERT INTO `antispam` (`id`, `timestamp`) VALUES ({0}, {1}) ON DUPLICATE KEY UPDATE `timestamp`={1}".format(self.id, int(time.time())))
	def column(self, name):
		value = self.db.query("SELECT `{}` FROM `antispam` WHERE `id`={}".format(name, self.id))
		return value[0][0]
	def increment(self, name):
		self.db.run("UPDATE `antispam` SET `{0}`=`{0}`+1 WHERE `id`={1}".format(name, self.id))
	def zero(self, name):
		self.db.run("UPDATE `antispam` SET `{}`=0 WHERE `id`={}".format(name, self.id))
	def count(self):
		return self.column("violations")
	def identical(self):
		return self.column("identical")
	def message(self):
		return str(self.column("message"))
	def time(self):
		return int(self.column("timestamp"))
	def spammed(self):
		self.increment("violations")
	def messaged(self, contents):
		print("{} => {}\t{} violations\t{} identical messages".format(self.message(), contents.encode('utf-8', "ignore"), self.count(), self.identical()))
		self.db.run("UPDATE `antispam` SET `timestamp`='{}' WHERE `id`={}".format(int(time.time()), self.id))
		if contents.encode('utf-8', "ignore") == self.message().encode('utf-8', "ignore") and int(time.time()) - self.time() < 300:
			self.increment("identical")
			return True
		else:
			self.db.run("UPDATE `antispam` SET `message`=%s WHERE `id`={}".format(self.id), [contents.encode('utf-8', "ignore")])
			self.zero("identical")
			return False

class Module(common.BaseModule):
	__name__ = "Anti-Spam"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client, True)
		self.server = common.getserver(self.client)
		self.silenced = discord.utils.get(self.server.roles, id="347946970385743889")
	async def silence(self, person, time):
		await self.client.add_roles(person, self.silenced)
		await asyncio.sleep(time * 60)
		await self.client.remove_roles(person, self.silenced)
	def run_punishment(self, person, time):
		self.client.loop.create_task(self.silence(person, time))
	async def punish(self, message):
		author = message.author
		user = SpamTables(author.id)
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
	async def on_message(self, message):
		if message.author == self.client.user or message.channel.is_private:
			return
		if message.channel.name in Settings.cancer_channels:
			if len(message.mentions) > 0:
				await self.client.delete_message(message)
			else:
				return
		await self.match_del(r'((\S\s?)\2{4,})', message)
		await self.match_del(r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{4,})', message)
		user = SpamTables(message.author.id)
		if user.messaged(message.content) and user.identical() > 3:
			self.punish(message)
