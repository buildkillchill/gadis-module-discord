import asyncio
import discord
import valve
import valve.rcon

import common

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Utility"
	__version__ = "1.05"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
		self.addcmd("roles", self.roles, "View a list of roles with corrisponding IDs")
		self.addcmd("report", self.report, "Report a someone", usage="`report USER`\nWhen prompted, give reason for report.")
		self.addcmd("gmod.say", self.say, "Say something through console", private=True, rank=9)
		self.addcmd("gmod.tsay", self.tsay, "Say something through console", private=True, rank=9)
		self.addcmd("gmod.csay", self.csay, "Say something through console", private=True, rank=9)
		self.addcmd("gmod.tsayc", self.tsayc, "Say something through console", private=True, rank=9)
	async def roles(self, args, pmsg):
		for server in self.client.servers:
			roleids = None
			for role in server.roles:
				if roleids == None:
					roleids = "{} ({})".format(role.name, role.id)
				else:
					roleids = "{}\n{} ({})".format(roleids, role.name, role.id)
			em = discord.Embed(title=server.id, description=roleids)
			em.set_author(name=server.name, icon_url=server.icon_url)
			await self.client.send_message(pmsg.channel, embed=em)
	async def report(self, args, pmsg):
		perp = " ".join(args[1:])
		await self.send(pmsg.channel, "In a single message, what did {} do? \n_Note: Waiting 3 minutes before sending a message or sending `cancel report` will cancel the report._".format(perp))
		reason = await self.getreply(180, pmsg.author, pmsg.channel)
		if reason == None or reason.content.lower() == "cancel report":
			await self.send(pmsg.channel, "The report cancelled!")
		else:
			await self.send(self.getchannel("admin"), "<@&312417207911186433>: {} is filing a _confidential_ report against {} for '{}'".format(pmsg.author.mention, perp, reason.content))
			await self.send(pmsg.channel, "Thank you for reporting the incident, {}. I have filed it to the Admins.".format(pmsg.author.mention))
	async def say(self, args, pmsg=None):
		valve.rcon.execute((Settings.RCON["host"], Settings.RCON["port"]), Settings.RCON["pass"], "say {}".format(" ".join(args[1:])))
	async def tsay(self, args, pmsg=None):
		valve.rcon.execute((Settings.RCON["host"], Settings.RCON["port"]), Settings.RCON["pass"], "ulx tsay \"{}\"".format(" ".join(args[1:])))
	async def csay(self, args, pmsg=None):
		valve.rcon.execute((Settings.RCON["host"], Settings.RCON["port"]), Settings.RCON["pass"], "ulx csay \"{}\"".format(" ".join(args[1:])))
	async def tsayc(self, args, pmsg=None):
		msg = ""
		for arg in args[1:]:
			if arg.endswith("\""): break
			msg = "{} {}".format(msg, arg)
		print("ulx tsaycolor \"{}\" {}".format(msg, args[-1]))
		valve.rcon.execute((Settings.RCON["host"], Settings.RCON["port"]), Settings.RCON["pass"], "ulx tsaycolor \"{}\" {}".format(msg, args[-1]))
