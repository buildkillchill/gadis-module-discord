import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Insult Reply"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
	async def on_message(self, message):
		msg = message.content.lower()
		if msg.startswith("idc") or msg.startswith("idgaf") or msg.startswith("i dont care") or msg.startswith("i don't care") or msg.startswith("i don't give a fuck") or msg.startswith("i dont give a fuck"):
			await self.send(message.channel, "No one gives a fuck that you don't give a fuck, so shut the fuck up and quit whining about it {}.".format(message.author.mention))
		elif re.search(r'(@here)', msg):
			await self.send(message.channel, "Fuck off {}".format(message.author.mention))
		elif re.search(r'(who is)', msg):
			await self.send(message.channel, "Who gives a fuck {}? No one, so shut up.".format(message.author.mention))
