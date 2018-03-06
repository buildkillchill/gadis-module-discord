import json, requests, re
import common
import mysql

class Module(common.BaseModule):
	__name__ = "Insult Reply"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
		self.db = mysql.default()
	async def on_message(self, message):
		msg = message.content.lower()
		for trigger in self.db.query("SELECT * FROM `insult_triggers`"):
			if re.search(trigger[0], msg):
				reply = self.db.query("SELECT * FROM `insult_replies` WHERE `id`={} LIMIT 1".format(trigger[1]))
				print(reply)
				if reply[2]:
					reply_text = reply[1].format(message.author.mention)
				else:
					reply_text = reply[1]
				await self.send(message.channel, reply_text)
