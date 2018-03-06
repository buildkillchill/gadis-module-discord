import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Mod Manager"
	def __init__(self, enabled, client=None, modules={}):
		common.BaseModule.__init__(self, enabled, client)
		self.mods = modules
		self.addcmd("enmod", self.enable, "Enable module", rank=9)
		self.addcmd("dismod", self.disable, "Disable module", rank=9)
	async def enable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		if mod in self.mods:
			self.mods[mod].enable()
			await self.send(pmsg.channel, "{} has been **enabled**".format(mod))
		else:
			await self.send(pmsg.channel, "{} does not exist".format(mod))
	async def disable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		if mod in self.mods:
			self.mods[mod].disable()
			await self.send(pmsg.channel, "{} has been **disabled**".format(mod))
		else:
			await self.send(pmsg.channel, "{} does not exist".format(mod))
