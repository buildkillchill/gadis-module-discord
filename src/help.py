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
	def set(self, enabled=True, client=None, modules={}):
		self.enabled = enabled
		self.client = client
		self.modules = modules
	async def show_module(self, channel, module):
		if not self.enabled: return
		if not module.has_commands(): return
		mod = discord.Embed(title="{} Module:".format(module.__name__))
		mod.set_author(name="Gadis", icon_url=self.client.user.avatar_url)
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
	async def show(self, channel):
		await self.send(channel, "Here is the help list for all modules.")
		for n in self.modules:
			module = self.modules[n]
			await self.show_module(channel, module)
	async def show_modules(self, channel, modules):
		await self.send(channel, "Here is the help list for the modules you have selected.")
		for n in modules:
			if n in self.modules:
				module = self.modules[n]
				await self.show_module(channel, module)
