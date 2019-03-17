import json, requests, re, os
import discord
import common
from settings import Settings

class Module(common.BaseModule):
	__name__ = "Mod Manager"
	__version__ = "1.05"
	def __init__(self, enabled, client=None, modules={}):
		common.BaseModule.__init__(self, enabled, None, client)
		self.mods = modules
		self.addcmd("enmod", self.enable, "Enable module", rank=Settings.OwnerRank)
		self.addcmd("dismod", self.disable, "Disable module", rank=Settings.OwnerRank)
		self.addcmd("version", self.version, "Get version info")
	async def enable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		try:
			obj = __import__(mod)
			logger.info("Initializing {}".format(mod))
			cls = getattr(obj, "Module")
			init = cls(True, db, client)
			modules[mod] = init
			self.mods[mod].enable()
			await self.send(pmsg.channel, "{} has been **enabled**".format(mod))
		except:
			await self.send(pmsg.channel, "{} does not exist or could not be loaded.".format(mod))
	async def disable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		handled = False
		if mod in self.mods:
			self.mods[mod].disable()
			del mod
			del self.mods[mod]
			handled = True
		if handled:
			await self.send(pmsg.channel, "{} has been **disabled**".format(mod))
		else:
			await self.send(pmsg.channel, "{} does not exist".format(mod))
	async def version(self, args, pmsg):
		l = list(set(list(self.mods.keys())))
		server = common.getserver(self.client)
		creator = discord.utils.get(server.members, id=str(Settings.People["creator"]))
		ver = "```\nVersion : {}\nCodename: {}```"
		em = discord.Embed(title="Version Info", description=ver.format(Settings.Version["code"], Settings.Version["name"]))
		em.set_author(name=creator.name, icon_url=creator.avatar_url)
		ver = "```\nSafe Name: {}\nVersion  : {}\nBound    : {}\nCommands : {}```"
		em.add_field(name=self.__name__,value=ver.format(__name__, self.__version__, hasattr(self, 'on_message') and callable(getattr(self, 'on_message')), self.has_commands()), inline=False)
		for mod in l:
			if mod == "modules": continue
			n = mod
			v = "0.00"
			b = False
			c = False
			if mod in self.mods:
				c = self.mods[mod].has_commands()
				v = self.mods[mod].__version__
				n = self.mods[mod].__name__
				b = hasattr(self.mods[mod], 'on_message') and callable(getattr(self.mods[mod], 'on_message'))
			em.add_field(name=n, value=ver.format(mod, v, b, c), inline=True)
		await self.client.send_message(pmsg.channel, embed=em)
