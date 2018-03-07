import asyncio
import discord

import common
import mysql

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Accounts"
	__version__ = "2.04"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
		self.addcmd("link", self.link, "Link your Steam and Discord to me. This allows for applying for admin and future features.", private=True)
		self.addcmd("+1inf", self.infract, "Add an infraction to user(s).", rank=10)
		self.addcmd("+.5inf", self.infract, "Add a half-infraction to user(s).", rank=10)
		self.addcmd("testinf", self.testinf, "Test infraction demotion message", rank=9)
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

