import discord
import asyncio
from steam import WebAPI as SteamAPI

import common
import mysql

class Module(asyncio.Protocol, common.BaseModule):
	__name__ = "Remote"
	def __init__(self, client):
		self.client = client
		self.db = mysql.default()
	def connection_made(self, transport):
		self.transport = transport
	def data_received(self, data):
		message = data.decode()
		words = message.split(' ')
		if words[0] == "test":
			self.run(self.send(self.client.get_channel('312405305759760394'), 'Test command received!'))
		elif words[0] == "shutdown":
			self.db.disconnect()
			self.run(self.client.logout())
		elif words[0] == "msg":
			msg = " ".join(words[2:])
			channel = words[1]
			ch=self.getchannel(channel)
			self.run(self.send(ch, msg))
		elif words[0] == "noadmin":
			server = words[1]
			self.run(self.no_admin(server))
		self.transport.close()

	async def no_admin(self,server):
		ch=self.getchannel("admin")
		last=False
		notify="<@&312417207911186433> There's no admin on shift in the {} server!".format(server)
		notify="There's no admin on shift in the {} server!".format(server)
		async for msg in self.client.logs_from(ch,limit=1):
			if msg.author == self.client.user and msg.content == notify:
				last=True
		if not last:
			self.run(self.send(ch,notify))
	def run(self,object):
		self.client.loop.create_task(object)
