
import asyncio
import discord

import common
import mysql

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Accounts"
	__version__ = "2.02"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
		self.addcmd("link", self.link, "Link your Steam and Discord to me. This allows for applying for admin and future features.", private=True)
		self.addcmd("+1inf", self.infract, "Add an infraction to user(s).", rank=Settings.OwnerRank)
		self.addcmd("+.5inf", self.infract, "Add a half-infraction to user(s).", rank=Settings.OwnerRank)
		self.addcmd("testinf", self.testinf, "Test infraction demotion message", rank=Settings.OwnerRank)
		self.addcmd("my-slogan-is", self.slogan, "Set your slogan", rank=Settings.Admin["rank"])
		self.addcmd("set-title", self.title, "Set admin title", rank=Settings.OwnerRank)
		self.addcmd("userinfo", self.info, "Get user info", private=True)
	async def info(self, args, message):
		user = None
		if len(message.mentions) > 0:
			user = message.mentions[0]
		elif len(args) > 1:
			try:
				id = int(args[1])
				user = await self.client.get_user_info(str(id))
			except:
				user = None
		if user == None:
			await self.send(message.channel, "Bad syntax bro")
		else:
			u = common.User.from_discord_id(self.client, user.id)
			linked = u == None
			em = discord.Embed(title="User Info",description="")
			em.set_author(user.name, icon_url=user.avatar_url)
			em.add_field("Display Name", user.display_name, False)
			em.add_field("ID", user.id, False)
			if linked: em.add_field("Gadis ID", u.ID(), False)
			if linked: em.add_field("Steam ID", u.steamID(), False)
			if linked: em.add_field("Steam64 ID", u.steamID64(), False)
			if linked: em.add_field("Rank", u.rank(), False)
			if linked: em.add_field("Infractions", u.infractions(), False)
			if linked: em.add_field("Locked", "Yes" if u.locked() else "No", False)
			em.add_field("Bot", "Yes" if user.bot else "No", False)
			em.add_field("Account Created", user.created_at, False)
			await self.sendembed(em)
	async def slogan(self, args, message):
		slogan = " ".join(args[1:])
		self.db.run("UPDATE `linked` SET `slogan`=%s WHERE `did`={}".format(message.author.id), [slogan])
		await self.send(message.channel, "{}'s new slogan is: {}".format(message.author.mention, slogan))
	async def title(self, args, message):
		title = common.strip_mentions(" ".join(args[1:]))
		self.db.run("UPDATE `linked` SET `title`=%s WHERE `did`={}".format(message.mentions[0].id), [title])
		await self.send(message.channel, "{}'s new title is: {}".format(message.mentions[0].mention, title))
	async def link(self, args, message):
		await self.send(message.author, "To finish the linking process, open this link in your browser: http://bkcservice.zenforic.com/link/?did={}".format(message.author.id))
	async def infract(self, args, message):
		if "+1inf" in message.content:
			amt=1
		elif "+.5inf" in message.content:
			amt=0.5
		else:
			return
		for member in message.mentions:
			user = common.User.from_discord_id(self.client, member.id)
			user.infract(amt)
			if user.infractions() >= Settings.MaxInfractions[user.rank()]:
				em = discord.Embed(title="Infractions Beyond Permissible Amount", description="The consequences are listed below.")
				em.set_author(name=message.author.name, icon_url=message.author.avatar_url)
				em.add_field(name="Demotion", value="You will be demoted to your previous rank and your infractions will be reset.")
				em.add_field(name="Account Lock", value="Your account will be locked from receiving promotions. This may be overridden at the descretion of Azicus. Begging or asking will only make things worse.")
				await self.send_embed(member, em)
				await user.setrank(user.previous_rank())
	async def testinf(self, args, message):
		for member in message.mentions:
			user = common.User.from_discord_id(self.client, member.id)
			em = discord.Embed(title="! TEST MESSAGE ! Infractions Beyond Permissible Amount ! TEST MESSAGE !", description="! TEST MESSAGE ! The consequences are listed below. ! TEST MESSAGE !")
			em.set_author(name=message.author.name, icon_url=message.author.avatar_url)
			em.add_field(name="Demotion", value="You will be demoted to your previous rank and your infractions will be reset.")
			em.add_field(name="Account Lock", value="Your account will be locked from receiving promotions. This may be overridden at the descretion of Azicus. Begging or asking will only make things worse.")
			em.add_field(name="THIS IS JUST A TEST", value="You will not actually get any of these consequences, as you did nothing wrong.")
			await self.send_embed(member, em)

