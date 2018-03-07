import json, requests, re
import discord
import common
import mysql

class Module(common.BaseModule):
	__name__ = "Insult Reply"
	__version__ = "2.42"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client, True)
	async def on_message(self, message):
		if not await common.BaseModule.on_message(self, message): return
		server = common.getserver(self.client)
		notilt = discord.utils.get(server.roles, id="420779120352296960")
		if notilt not in message.author.roles: return
		msg = re.sub('[^a-z0-9 ]', '', message.content.lower(), flags=re.UNICODE)
		for trigger in self.db.query("SELECT * FROM `insult_triggers`"):
			if re.search(trigger[0], msg):
				reply = self.db.query("SELECT * FROM `insult_replies` WHERE `id`={}".format(trigger[1]))
				reply = reply[0]
				if reply[2]:
					reply_text = reply[1].format(message.author.mention)
				else:
					reply_text = reply[1]
				await self.send(message.channel, reply_text)
