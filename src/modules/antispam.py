import re
import common

class Module(common.BaseModule):
	__name__ = "Anti-Spam"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client, True)
		self.cancer_channels = []
		self.cancer_channels.append("cancer")
		self.violations = {}
	async def silence(self, person, time):
		server = Common.getserver(self.client)
		silenced = discord.utils.get(server.roles, id="347946970385743889")
		await self.client.add_roles(person, silenced)
		await asyncio.sleep(time * 60)
		await self.client.remove_roles(person, silenced)
	def run_punishment(self, person, time):
		self.client.loop.create_task(self.silence(person, time))
	async def punish(self, author, message):
		await self.client.delete_message(message)
		if self.violations[author] == None:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed.".format(author.mention))
			self.violations[author] = 0
		elif self.violations[author] < 5:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for 5 minutes.".format(author.mention))
			self.run_punishment(author, 5)
		elif self.violations[author] < 10:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for 30 minutes.".format(author.mention))
			self.run_punishment(author, 30)
		elif self.violations[author] < 20:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for 1 hour.".format(author.mention))
			self.run_punishment(author, 60)
		elif self.violations[author] < 30:
			await self.client.send_message(message.channel, "There is no need to spam your keyboard {}. Your message will be removed and you will be silenced for 5 hours.".format(author.mention))
			self.run_punishment(author, 5 * 60)
		elif self.violations[author] >= 30:
			msg = await self.self.client.send_message(message.channel, "{} will be kicked for spamming in 5s".format(author.mention))
			time = 5
			while time > 0:
				time = time - 1
				await asyncio.sleep(1)
				await self.self.client.edit_message(msg, "{} will be kicked for spamming 30+ times in {}s".format(author.mention, time))
			await self.self.client.edit_message(msg, "Kicking {}...".format(author.mention, time))
			await self.client.kick(author)
			await self.self.client.edit_message(msg, "Kicked {} right in the nut sack. Let 'em brew in pain for a bit. :wink:".format(author.mention, time))
		self.violations[author] = self.violations[author] + 1
	async def match_del(self, pattern, message):
		match = re.search(pattern, message.content.lower())
		if match:
			await self.punish(message.author, message)
	async def on_message(self, message):
		if message.author == self.client.user or message.channel.is_private:
			return
		if message.channel.name in self.cancer_channels:
			if len(message.mentions) > 0:
				await self.client.delete_message(message)
			else:
				return
		await self.match_del(r'((\S\s?)\2{4,})', message)
		await self.match_del(r'((\<:[a-z0-9\-_]+:[0-9]+\>\s?)\2{4,})', message)
