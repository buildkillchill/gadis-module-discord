import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Mod Manager"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client, True)
		self.addcmd("enmod", self.enable, "Enable module", rank=9)
		self.addcmd("dismod", self.disable, "Disable module", rank=9)
	async def enable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		await self.send(pmsg.channel, "This functionality is not available yet, so I cannot enable {} for you. Please use the database administration tool.".format(mod))
	async def disable(self, args, pmsg):
		mod = ("".join(args[1:])).lower()
		await self.send(pmsg.channel, "This functionality is not available yet, so I cannot disable {} for you. Please use the database administration tool.".format(mod))
