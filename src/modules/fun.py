import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Fun"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
		self.addcmd("woof", self.woof, "Lovely puppies...")
		self.addcmd("meow", self.meow, "Lovely kitties...")
		self.horses = {}
	async def meow(self, args, pmsg):
		resp = requests.get(url="http://random.cat/meow")
		data = json.loads(resp.text)
		url = data["file"]
		await self.send(pmsg.channel, url)
	async def woof(self, args, pmsg):
		resp = requests.get(url="https://random.dog/woof")
		url = "https://random.dog/{}".format(resp.text)
		await self.send(pmsg.channel, url)
	async def on_message(self, message):
		msg = message.content.lower()
		if msg.startswith("idc") or msg.startswith("idgaf") or msg.startswith("i dont care") or msg.startswith("i don't care") or msg.startswith("i don't give a fuck") or msg.startswith("i dont give a fuck"):
			await self.send(message.channel, "No one gives a fuck that you don't give a fuck, so shut the fuck up and quit whining about it.")
		elif re.search(r'((🐴\s?)\2{4,})', msg):
			print(self.horses)
			if not message.author.id in self.horses:
				self.horses[message.author.id] = 0
			if self.horses[message.author.id] < 5:
				await self.send(message.author, "Your prayers to the :horse: God, Azicus, has been heard!")
				self.horses[message.author.id] = self.horses[message.author.id] + 1
			elif self.horses[message.author.id] == 5:
				await self.send(message.author, "Your prayers to the :horse: God, Azicus, have been ANSWERED!!!!")
				await self.send(self.client.get_channel("347437194488840202"), ".award 150 {}".format(message.author.mention))
		elif len(message.mentions) > 0:
			for mention in message.mentions:
				print(mention)
				if str(mention) == "@here":
					await self.send(message.channel, "Fuck off {}".format(message.author.mention))
