import discord
import asyncio
from steam import WebAPI as SteamAPI

import common
import mysql
from settings import Settings

class Module(asyncio.Protocol, common.BaseModule):
	__name__ = "Remote"
	def __init__(self, client):
		common.BaseModule.__init__(self, True, client)
		self.transport = None
	def connection_made(self, transport):
		if self.transport == None:
			transport.send("CONNECTION ALREADY ESTABLISHED")
			transport.close()
			self.logger.info("Additional connection attempt thwarted.")
			return
		self.transport = transport
		self.logger.info("Connection from {} established.".format(transport.get_extra_info('peername'))
	def data_received(self, data):
		message = data.decode()
		words = message.split(' ')
		self.logger.debug("Data from {} received.".format(self.transport.get_extra_info('peername')))
		self.logger.debug("Data Contents:\n{}".format(data))
		if words[0] == "shutdown":
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
		self.logger.info("Closing network transport...")
		self.transport.close()
		self.transport = None

	async def no_admin(self, server):
		ch=self.getchannel("admin")
		last=False
		notify="<@&{}> There's no admin on shift in the {} server!".format(Settings.Ranks[Settigns.Admin["rank"]][0], server)
		notify="There's no admin on shift in the {} server!".format(server)
		async for msg in self.client.logs_from(ch,limit=1):
			if msg.author == self.client.user and msg.content == notify:
				last=True
		if not last:
			self.run(self.send(ch,notify))
	def run(self, object):
		self.client.loop.create_task(object)
