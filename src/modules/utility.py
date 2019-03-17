import asyncio
import discord

import common

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Utility"
	__version__ = "1.09"
	def __init__(self, enabled, db, client=None):
		common.BaseModule.__init__(self, enabled, db, client, True)
		self.addcmd("roles", self.roles, "View a list of roles with corrisponding IDs")
		self.addcmd("report", self.report, "Report a someone", usage="`report USER`\nWhen prompted, give reason for report.")
		self.addcmd("%clear", self.clear, "Clear channel with conditions", usage="`%clear [X messages]`\nJust `%clear` to begin clearing a channel.", rank=Settings.OwnerRank)
		self.addcmd("gmod.say", self.say, "Say something through console", private=True, rank=Settings.OwnerRank)
		self.addcmd("gmod.tsay", self.tsay, "Say something through console", private=True, rank=Settings.OwnerRank)
		self.addcmd("gmod.csay", self.csay, "Say something through console", private=True, rank=Settings.OwnerRank)
		self.addcmd("gmod.tsayc", self.tsayc, "Say something through console", private=True, rank=Settings.OwnerRank)
		self.addcmd("+sqlq", self.sql, "Execute SQL query for results", rank=Settings.OwnerRank)
		self.addcmd("+sqle", self.sql, "Execute SQL query", rank=Settings.OwnerRank)
		self.addcmd("inv", self.repeats, "Show the invite link")
		self.addcmd("rtfa", self.repeats, "Read The Announcements", rank=Settings.Admin["rank"])
		self.addcmd("+subme", self.role_subs, "Subscribe to role-specific notifications", usage="`+subme EligibleRole`; do not @mention the role")
	async def role_subs(self, args, pmsg):
		if len(args) == 1:
			await self.send(pmsg.channel, "Please specify a role to subscribe to.")
			return
		selectedRole = " ".join(args[1:])
		roleValid = False
		for role in pmsg.server.roles:
			if role.name == selectedRole and selectedRole in Settings.Subs:
				roleValid = True
				givenRole = [role]
				try:
					await self.client.add_roles(pmsg.author, *givenRole)
					em = discord.Embed(title="You have subscribed to...", description=Settings.Subs[selectedRole])
					em.set_author(name=server.name, icon_url=server.icon_url)
					await self.client.send_message(pmsg.channel, embed=em)
					self.logger.debug("We got past adding embed. value to description is " + Settings.Subs[selectedRole] + "with str() is " + str(Settings.Subs[selectedRole]))
				except HTTPException:
					await self.send(pmsg.channel, "I couldn't give you the role! Are you already subscribed?")
				except Exception as e:
					self.logger.error("Unhandled error happened in rolesubs: " + str(e))
				finally:
					break
		if not roleValid:
			await self.send(pmsg.channel, "Invalid input, please specify a subscriber role.")
	async def sql(self, args, pmsg):
		query = " ".join(args[1:])
		if args[0].lower() == "+sqlq":
			res = self.db.query(query)
			if len(res) > 0:
				i = 1
				for row in res:
					v = ""
					for col in row:
						v = "{}{},".format(v, col)
					v = v[:-1]
					text = "Row {}:\n`{}`".format(i, v)
					await self.send(pmsg.channel, text)
					i += 1
			else:
				await self.send(pmsg.channel, "No results")
		else:
			self.db.run(query)
	async def repeats(self, args, pmsg):
		await self.send(pmsg.channel, Settings.Repeats[args[0].lower()])
	async def clear(self, args, pmsg):
		nargs = common.strip_mentions(" ".join(args[1:])).split(" ")
		if len(nargs) == 0 or nargs[0] == "":
			await self.logiter(pmsg.channel, mentions=pmsg.mentions)
		elif len(nargs) == 1:
			await self.logiter(pmsg.channel, limit=nargs[0], mentions=pmsg.mentions)
		else:
			await self.send(pmsg.channel, "Too many arguments")
	async def logiter(self, channel, *, limit=None, mentions=None):
		if limit == None:
			while True:
				counter = 0
				async for message in self.client.logs_from(channel, limit=500):
					counter += 1
					if self.check_author(message, mentions):
						await self.client.delete_message(message)
						await asyncio.sleep(0.5)
				if counter < 500:
					break
				await asyncio.sleep(15)
		else:
			try:
				max = int(limit)
				while max > 500:
					counter = 0
					async for message in self.client.logs_from(channel, limit=500):
						counter += 1
						if self.check_author(message, mentions):
							await self.client.delete_message(message)
							await asyncio.sleep(0.5)
					max -= counter
					if counter < 500:
						break
					await asyncio.sleep(15)
				async for message in self.client.logs_from(channel, limit=max):
					if self.check_author(message, mentions):
						await self.client.delete_message(message)
						await asyncio.sleep(0.2)
			except ValueError:
				await self.send(channel, "{} is not a valid number".format(limit))
	def check_author(self, message, mentions):
		if mentions == None or len(mentions) == 0:
			return True
		return message.author in mentions
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
			await self.send(self.getchannel("admin"), "<@&{}>: {} is filing a _confidential_ report against {} for '{}'".format(Settings.Ranks[Settings.Admin["rank"]][0], pmsg.author.mention, perp, reason.content))
			await self.send(pmsg.channel, "Thank you for reporting the incident, {}. I have filed it to the Admins.".format(pmsg.author.mention))
	async def say(self, args, pmsg=None):
		common.runrcon("say {}".format(" ".join(args[1:])))
	async def tsay(self, args, pmsg=None):
		common.runrcon("ulx tsay \"{}\"".format(" ".join(args[1:])))
	async def csay(self, args, pmsg=None):
		common.runrcon("ulx csay \"{}\"".format(" ".join(args[1:])))
	async def tsayc(self, args, pmsg=None):
		common.runrcon("ulx tsaycolor {}".format(" ".join(args[1:])))
