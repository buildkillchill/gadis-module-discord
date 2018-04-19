
import asyncio
import discord
from random import randint

import common

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Accounts"
	__version__ = "2.02"
	def __init__(self, enabled, db, client=None):
		common.BaseModule.__init__(self, enabled, db, client)
		self.addcmd("link", self.link, "Link your Steam and Discord to me. This allows for applying for admin and future features.", private=True)
		self.addcmd("+1inf", self.infract, "Add an infraction to user(s).", rank=Settings.OwnerRank)
		self.addcmd("+.5inf", self.infract, "Add a half-infraction to user(s).", rank=Settings.OwnerRank)
		self.addcmd("testinf", self.testinf, "Test infraction demotion message", rank=Settings.OwnerRank)
		self.addcmd("my-slogan-is", self.slogan, "Set your slogan", rank=Settings.Admin["rank"])
		self.addcmd("set-title", self.title, "Set admin title", rank=Settings.OwnerRank)
		self.addcmd("userinfo", self.info, "Get user info", private=True)
		self.addcmd("unlink-my-account", self.unlink, "Unlink and remove yourself from our accounts database", private=True)
		self.addcmd("force-link", self.flink, "Force link user", rank=Settings.OwnerRank)
	async def flink(self, args, message):
		if not len(message.mentions) == 1:
			await self.send(message.channel, "Please mention some poor fuck to link to this Steam ID.")
			return
		nargs = common.strip_mentions(" ".join(args[1:])).split(" ")
		self.logger.debug(" ".join(nargs))
		if not len(nargs) == 1:
			await self.send(message.channel, "Learn to use the damn commands.")
			return
		try:
			sid = int(nargs[0])
		except ValueError:
			await self.send(message.channel, "Are you a moron? Steam IDs are integers...")
			return
		except:
			await self.send(message.channel, "I think I'm stupid. Or broken. I don't know which. Either way I was unable to convert the arg you provided to an integer.")
			return
		query = self.db.query("SELECT * FROM `linked` WHERE `sid`={} OR `did`={}".format(sid, message.mentions[0].id))
		if len(query) > 0:
			await self.send(message.channel, "This account is already linked ijiot")
			return
		self.db.run("DELETE FROM `link` WHERE `did`={}".format(message.mentions[0].id))
		self.db.run("INSERT INTO `linked` (`sid`,`did`) VALUES ({},{})".format(sid, message.mentions[0].id))
	async def unlink(self, args, message):
		await self.send(message.channel, "To confirm your unlink please type `I DON'T LIKE BEING LINKED, PLEASE FORGET ME.`\nIt must be _exactly_ that, including the upper case and symbols. You have 60 seconds to do so, starting now.")
		reply = await self.getreply(60, message.author, message.channel)
		if reply.contents == "I DON'T LIKE BEING LINKED, PLEASE FORGET ME.":
			self.db.run("DELETE FROM `linked` WHERE `did`={}".format(message.author.id))
			self.db.run("DELETE FROM `link` WHERE `did`={}".format(message.author.id))
			await self.send(message.channel, "You have been forgotten.")
	async def info(self, args, message):
		user = None
		if len(message.mentions) > 0:
			user = discord.utils.get(common.getserver(self.client).members, id=str(message.mentions[0].id))
		elif len(args) > 1:
			try:
				id = int(args[1])
				user = discord.utils.get(common.getserver(self.client).members, id=str(id))
			except ValueError:
				await self.send(message.channel, "Could not convert {} to an integer".format(args[1]))
				return
			except:
				logger.error("Unhandled error happened in userinfo")
				return
		else:
			await self.send(message.channel, "Bad syntax")
			return
		if user == None:
			await self.send(message.channel, "No user by that ID was found")
		else:
			u = common.User.from_discord_id(self.client, self.db, user.id)
			linked = False if u == None else True
			em = discord.Embed(title="",description="")
			em.set_author(name=user.name, icon_url=user.avatar_url)
			self.add_field(em, "Display Name:", user.display_name, False)
			self.add_field(em, "ID:", user.id, False)
			if linked: self.add_field(em, "Gadis ID:", u.ID(), False)
			if linked: self.add_field(em, "Steam ID:", u.steamID(), False)
			if linked: self.add_field(em, "Steam64 ID:", u.steamID64(), False)
			if linked: self.add_field(em, "Rank:", u.rank(), False)
			if linked: self.add_field(em, "Infractions:", u.infractions(), False)
			if linked: self.add_field(em, "Locked:", "Yes" if u.locked() else "No", False)
			self.add_field(em, "Bot:", "Yes" if user.bot else "No", False)
			self.add_field(em, "Account Created:", "{} UTC".format(user.created_at), False)
			await self.send_embed(message.channel, em)
	async def slogan(self, args, message):
		slogan = " ".join(args[1:])
		self.db.run("UPDATE `linked` SET `slogan`=%s WHERE `did`={}".format(message.author.id), [slogan])
		await self.send(message.channel, "{}'s new slogan is: {}".format(message.author.mention, slogan))
	async def title(self, args, message):
		title = common.strip_mentions(" ".join(args[1:]))
		self.db.run("UPDATE `linked` SET `title`=%s WHERE `did`={}".format(message.mentions[0].id), [title])
		await self.send(message.channel, "{}'s new title is: {}".format(message.mentions[0].mention, title))
	async def link(self, args, message):
		query = self.db.query("SELECT `did` FROM `linked` WHERE `did`={}".format(message.author.id))
		if len(query) > 0:
			await self.send(message.author, "Your account is already linked")
			return
		query = self.db.query("SELECT `code` FROM `link` WHERE `id`={} AND `used`=FALSE".format(message.author.id))
		if len(query) > 0:
			code = query[0][0]
		else:
			code = 0
			while code == 0:
				code = randint(10000, 99999)
				query = self.db.query("SELECT `id` FROM `link` WHERE `code`={} AND `used`=FALSE".format(code))
				if len(query) > 0:
					code = 0
					await asyncio.sleep(0.2)
			self.db.run("INSERT INTO `link` (`id`,`code`) VALUES ({0},{1}) ON DUPLICATE KEY UPDATE `id`={0},`used`=FALSE".format(message.author.id, code))
		await self.send(message.author, "Thank you for starting the linking process. To complete the linking process, please get on the BKC GMod server and send `!link {}` in chat.".format(code))
	async def infract(self, args, message):
		if "+1inf" in message.content:
			amt=1
		elif "+.5inf" in message.content:
			amt=0.5
		else:
			return
		for member in message.mentions:
			user = common.User.from_discord_id(self.client, self.db, member.id)
			user.infract(amt)
			if user.infractions() >= Settings.MaxInfractions[user.rank()]:
				em = discord.Embed(title="Infractions Beyond Permissible Amount", description="The consequences are listed below.")
				em.set_author(name=message.author.name, icon_url=message.author.avatar_url)
				self.add_field(em, "Demotion", "You will be demoted to your previous rank and your infractions will be reset.")
				self.add_field(em, "Account Lock", "Your account will be locked from receiving promotions. This may be overridden at the descretion of Azicus. Begging or asking will only make things worse.")
				await self.send_embed(member, em)
				await user.setrank(user.previous_rank())
	async def testinf(self, args, message):
		for member in message.mentions:
			user = common.User.from_discord_id(self.client, self.db, member.id)
			em = discord.Embed(title="! TEST MESSAGE ! Infractions Beyond Permissible Amount ! TEST MESSAGE !", description="! TEST MESSAGE ! The consequences are listed below. ! TEST MESSAGE !")
			em.set_author(name=message.author.name, icon_url=message.author.avatar_url)
			self.add_field(em, "Demotion", "You will be demoted to your previous rank and your infractions will be reset.")
			self.add_field(em, "Account Lock", "Your account will be locked from receiving promotions. This may be overridden at the descretion of Azicus. Begging or asking will only make things worse.")
			self.add_field(em, "THIS IS JUST A TEST", "You will not actually get any of these consequences, as you did nothing wrong.")
			await self.send_embed(member, em)
	def add_field(self, em, name, value, inline=True):
		em.add_field(name=name, value=value, inline=inline)
