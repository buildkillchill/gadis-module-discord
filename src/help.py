import discord
import asyncio
import textwrap

import common

from settings import Settings

class Module(common.BaseModule):
	def __init__(self, enabled=True, client=None, modules={}):
		self.enabled = enabled
		self.client = client
		self.modules = modules
		print(__file__)
	def set(self, enabled=True, client=None, modules={}):
		self.enabled = enabled
		self.client = client
		self.modules = modules
	async def show(self, channel):
		if not self.enabled:
			return
		await self.send(channel, "You have triggered the Help Module.")
		for n in self.modules:
			module = self.modules[n]
			mod = discord.Embed(title="{} Module:".format(module.__name__))
			mod.set_author(name="BKC Services", icon_url=self.client.user.avatar_url)
			for command in module.getcommands():
				helptext = module.gethelp(command)
				helptext = textwrap.fill(helptext, 25)
				if module.has_usage(command):
					helptext = "{}\n**Usage:** {}".format(helptext, module.get_usage(command))
				if module.is_private(command):
					helptext = "{}\n**DM _ONLY_**".format(helptext)
				helptext = "{}\n**Access:** {}".format(helptext, Settings.RankName[module.min_rank(command)])
				mod.add_field(name=command, value=helptext, inline=True)
			await self.send_embed(channel, mod)
