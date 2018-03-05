import re
import common

class Module(common.BaseModule):
	__name__ = "Anti-Spam"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client, True)
		self.cancer_channels = []
		self.cancer_channels.append("cancer")
	async def match_del(self, pattern, message):
		match = re.search(pattern, message.content.lower())
		if match:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}".format(message.author.mention))
			await self.client.delete_message(message)

	async def on_message(self, message):
		if message.author == self.client.user:
			return
		if message.channel.name in self.cancer_channels:
			if len(message.mentions) > 0:
				await self.client.delete_message(message)
			else:
				return
		await self.match_del(r'((\S\s?)\2{4,})', message)
		await self.match_del(r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{4,})', message)
