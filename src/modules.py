import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Mod Manager"
	__version__ = "1.00"
	def __init__(self, enabled, client=None, modules={}, advanced={}):
		common.BaseModule.__init__(self, enabled, client)
		self.mods = modules
		self.advm = advanced
		self.addcmd("enmod", self.enable, "Enable module", rank=9)
		self.addcmd("dismod", self.disable, "Disable module", rank=9)
		self.addcmd("version", self.version, "Get version info")
	async def enable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		handled = False
		if mod in self.mods:
			self.mods[mod].enable()
			handled = True
		elif mod in self.advm:
			self.advm[mod].enable()
			handled = True
		if handled:
			await self.send(pmsg.channel, "{} has been **enabled**".format(mod))
		else:
			await self.send(pmsg.channel, "{} does not exist".format(mod))
	async def disable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		handled = False
		if mod in self.mods:
			self.mods[mod].disable()
			handled = True
		elif mod in self.advm:
			self.advm[mod].disable()
			handled = True
		if handled:
			await self.send(pmsg.channel, "{} has been **disabled**".format(mod))
		else:
			await self.send(pmsg.channel, "{} does not exist".format(mod))
	async def version(self, args, pmsg):
		list = list(set(self.mods.keys() + self.advm.keys()))
		server = common.getserver(self.client)
		creator = discord.utils.get(server.members, id=str(Settings.creatorid))
		ver = "```\nVersion : {}\nCodename: {}```"
		em = discord.Embed(title="Version Info", description=ver.format(Settings.version, Settings.codename))
		em.set_author(name=creator.nick, icon_url=creator.avatar_url)
		ver = "```\nSafe Name: {}\nVersion  : {}\nBound    : {}\nCommands : {}```"
		for mod in list:
			n = mod
			v = "0.00"
			b = False
			c = False
			if mod in self.advm:
				b = True
				v = self.advm[mod].__version__
				n = self.advm[mod].__name__
			if mod in self.mods:
				c = True
				v = self.mods[mod].__version__
				n = self.advm[mod].__name__
			em.add_field(name=n, value=ver.format(mod, v, b, c), inline=True)
		await self.client.send_message(pmsg.channel, embed=em)
