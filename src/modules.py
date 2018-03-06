import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Mod Manager"
	def __init__(self, enabled, client=None, modules={}, advanced={}):
		common.BaseModule.__init__(self, enabled, client)
		self.mods = modules
		self.advm = advanced
		self.addcmd("enmod", self.enable, "Enable module", rank=9)
		self.addcmd("dismod", self.disable, "Disable module", rank=9)
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
