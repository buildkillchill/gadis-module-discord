import asyncio
import discord
import valve.steam.id
import valve.rcon
import logging
import re

from settings import Settings

def strip_mentions(text):
	return re.sub("(@.*#[0-9]{4}|\<@\!?[0-9]+\>)", "", text).strip()

def runrcon(cmd):
	 valve.rcon.execute((Settings.RCON["host"], Settings.RCON["port"]), Settings.RCON["pass"], cmd)

def getmodulestatus(db, name):
	db.run("INSERT IGNORE INTO `modules` (`name`) VALUES (%s)", [name])
	status = db.query("SELECT `enabled` FROM `modules` WHERE `name`=%s", [name])
	status = status[0][0]
	return status

def setmodulestatus(db, name, enabled):
	db.run("INSERT INTO `modules` (`name`,`enabled`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `enabled`=%s", [name, enabled, enabled])

def getserver(client):
	return client.get_server(str(Settings.ServerID))

def getroles(client, db, rank):
	server = getserver(client)
	roles = []
	for rank in Settings.Ranks[rank]:
		roles.append(discord.utils.get(server.roles, id=str(rank)))
	return roles

def getgmodrank(rank):
	rank = db.query("SELECT `name` FROM `ranks` WHERE `id`={}".format(rank))
	return rank[0][0]

def getmember(client, user):
	server = getserver(client)
	return discord.utils.get(server.members, id=str(user.discordID()))

def getrank(db, id):
	try:
		return db.query("SELECT `rank` FROM `linked` WHERE `did`={}".format(id))[0][0]
	except:
		return 1

class LoggerExtension(logging.getLoggerClass()):
	def __init__(self, *args, **kwargs):
		super(LoggerExtension, self).__init__(*args, **kwargs)
	def extra(self, msg, *args, **kwargs):
		self.log(15, msg, *args, **kwargs)

class BaseModule():
	def __init__(self, enabled, db, client, raw=False):
		self.enabled = enabled
		self.raw = raw
		self.client  = client
		self.commands = {}
		self.help = {}
		self.minrank = {}
		self.usage = {}
		self.private = []
		self.db = db
		logging.setLoggerClass(LoggerExtension)
		self.logger = logging.getLogger("GADIS.MOD.{}".format("".join(self.__name__.split())))
		self.logger.extra("{} Base Initialization Completed.".format(self.__name__))
	async def on_message(self, message):
		if self.enabled and not message.author == self.client.user:
			return True
		else:
			return False
	def receive(self, cmd, args, pmsg):
		if pmsg.channel.is_private:
			channel = "by private message"
		else:
			channel = "in #".format(pmsg.channel.name)
		if cmd in self.commands and self.enabled:
			self.logger.info("User with ID {} has sent command '{}' {}".format(pmsg.author.id, cmd, channel.mention))
			self.client.loop.create_task(self.commands[cmd](args, pmsg))
			return True
		else:
			return False
	def enable(self):
		self.enabled = True
		setmodulestatus(self.db, __file__[:-4], True)
	def disable(self):
		self.enabled = False
		setmodulestatus(self.db, __file__[:-4], False)
	async def send(self, channel, message):
		return await self.client.send_message(channel, message)
	async def edit(self, message, new_message):
		return await self.client.edit_message(message, new_message)
	async def send_embed(self, channel, message):
		return await self.client.send_message(channel, embed=message)
	async def edit_embed(self, message, new_message):
		return await self.client.edit_message(message, embed=new_message)
	async def delete(self, message):
		return await self.client.delete(message)
	async def getreply(self, timeout, author, channel):
		return await self.client.wait_for_message(timeout=timeout, author=author, channel=channel)
	async def getuser(self, id):
		return await self.client.get_user_info(id)
	def addcmd(self, command, funct, help, *, usage=None, rank=1, private=False):
		self.commands[command] = funct
		self.help[command] = help
		if private:
			self.private.append(command)
		if rank != 1:
			self.minrank[command] = rank
		if usage != None:
			self.usage[command] = usage
	def getchannel(self, name):
		return discord.utils.get(getserver(self.client).channels, name=name)
	def getrank(self, id):
		return self.db.query("SELECT `rank` FROM `linked` WHERE `did`={}".format(id))[0][0]
	def has_command(self, command):
		return command in self.commands
	def has_commands(self):
		return len(self.commands) > 0
	def getmember(self, id):
		server = getserver(self.client)
		return discord.utils.get(server.members, id=str(id))
	def getcommands(self):
		commands = []
		for command in self.commands:
			commands.append(command)
		return commands
	def gethelp(self, command):
		return self.help[command]
	def min_rank(self, command):
		if command in self.minrank:
			return self.minrank[command]
		else:
			return 1
	def permissible(self, command, rank, private):
		if command in self.minrank and rank < self.minrank[command]:
			return False
		elif command in self.private and not private:
			return False
		else:
			return True
	def infractions(self):
		res = self.db.query("SELECT `infractions` FROM `linked` WHERE `id`={}".format(self.id["id"]))
		try:
			return res[0][0]
		except:
			return 0
	def previous_rank(self):
		res = self.db.query("SELECT `previous_rank` FROM `linked` WHERE `id`={}".format(self.id["id"]))
		try:
			return res[0][0]
		except:
			return 1
	def is_private(self, command):
		return command in self.private
	def has_usage(self, command):
		return command in self.usage
	def get_usage(self, command):
		return self.usage[command]
	def bind_on_message(self):
		return self.raw

class Steam():
	@staticmethod
	def ID64(steamID):
		return valve.steam.id.SteamID.from_text(steamID).__int__()
	@staticmethod
	def ID(steam64):
		return valve.steam.id.SteamID.from_community_url("http://steamcommunity.com/profiles/{}".format(steam64)).__str__()
class User(BaseModule):
	def __init__(self, client, db, id, did, sid, sid64):
		self.id = {}
		self.id["id"] = id
		self.id["discord"] = did
		self.id["steam"] = sid
		self.id["steam64"] = sid64
		self.client = client
		self.db = db
	def ID(self):
		return self.id["id"]
	def steamID(self):
		return self.id["steam"]
	def steamID64(self):
		return self.id["steam64"]
	def discordID(self):
		return self.id["discord"]
	async def discord(self):
		return await self.client.get_user_info(self.id["discord"])
	def rank(self):
		return self.getcol("rank")
	def roles(self):
		rank = self.rank()
		return list(Settings.Ranks[rank])
	def lock(self):
		self.db.run("UPDATE `linked` SET `locked`=True WHERE `id`={}".format(self.id["id"]))
	def locked(self):
		return self.getcol("locked")
	def hours(self):
		return self.getcol("hours")
	def infractions(self):
		return self.getcol("infractions")
	def previous_rank(self):
		return self.getcol("previous_rank")
	def donated(self):
		return self.getcol("donated")
	def bday(self):
		return self.getcol("birthday")
	def getcol(self, name):
		return self.getfcol(name, "linked", self.id["id"])
	def getfcol(self, name, table, id):
		value = self.db.query("SELECT `{}` FROM `{}` WHERE `id`={}".format(name, table, id))
		return value[0][0]
	def setbday(self, date):
		self.db.run("UPDATE `linked` SET `birthday`=%s WHERE `id`={}".format(id), [date])
	async def setrank(self, rank, reason=None, activate_lock=True):
		if (self.rank() < rank and self.locked()) or self.rank() == rank: return

		if self.rank() < rank:
			await self.send(self.getchannel("general"), "Congratulations for your promotion, <@{}>!".format(self.discordID()))
		elif self.rank() > rank:
			if reason == None:
				await self.send(await self.discord(), "You have been demoted.")
			else:
				await self.send(await self.discord(), reason)
		else:
			return

		if activate_lock and self.rank() > rank:
			self.lock()

		member = getmember(self.client, self)
		roles = getroles(self.client, self.db, rank)
		prev = getroles(self.client, self.db, self.previous_rank())
		ranked_roles = []
		for key, value in Settings.Ranks.items():
			for rid in value:
				ranked_roles.append(rid)
		for role in member.roles:
			if "everyone" in role.name: continue
			if int(role.id) in ranked_roles:
				print("{} ({}) is a ranked role. Removing it from {}".format(role.id, role.name, member.id))
				await self.client.remove_roles(member, role)
		for role in roles:
			print("Adding {} ({}) to {}.".format(role.id, role.name, member.id))
			await self.client.add_roles(member, role)
		if self.rank() < rank:
			for role in prev:
				print("Adding {} ({}) to {}.".format(role.id, role.name, member.id))
				await self.client.add_roles(member, role)
		self.db.run("UPDATE `linked` SET `rank`={} WHERE `id`={}".format(rank, self.id["id"]))
		runrcon("ulx adduserid {} {}".format(self.steamID(), getgmodrank(self.db, rank)))
	def infract(self, amt):
		self.db.run("UPDATE `linked` SET `infractions`=`infractions`+{} WHERE `id`={}".format(amt, self.id["id"]))
	@staticmethod
	def from_steam_id(client, db, sid):
		sid64 = Steam.ID64(sid)
		account = db.query("SELECT `id`,`did` FROM `linked` WHERE `sid`={}".format(sid64))
		account = account[0]
		id = account[0]
		did = account[1]
		return User(client, db, id, did, sid, sid64)
	@staticmethod
	def from_steam_id64(client, db, sid64):
		sid = Steam.ID(sid64)
		account = db.query("SELECT `id`,`did` FROM `linked` WHERE `sid`={}".format(sid64))
		account = account[0]
		id = account[0]
		did = account[1]
		return User(client, db, id, did, sid, sid64)
	@staticmethod
	def from_discord_id(client, db, did):
		account = db.query("SELECT `id`,`sid` FROM `linked` WHERE `did`={}".format(did))
		if len(account) == 0:
			return None
		account = account[0]
		id = account[0]
		sid64 = account[1]
		sid = Steam.ID(sid64)
		return User(client, db, id, did, sid, sid64)
	@staticmethod
	def from_id(client, db, id):
		account = db.query("SELECT `did`,`sid` FROM `linked` WHERE `id`={}".format(id))
		account = account[0]
		did = account[0]
		sid64 = account[1]
		sid = Steam.ID(sid64)
		return User(client, db, id, did, sid, sid64)
