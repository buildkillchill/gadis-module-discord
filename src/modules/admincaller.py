import json, requests, re
import common

class Module(common.BaseModule):
	__name__ = "Admin Caller"
	__version__ = "1.00"
	def __init__(self, enabled, db, client=None):
		common.BaseModule.__init__(self, enabled, db, client, True)
		client.loop.create_task(self.Check())
	async def Check(self):
		while True:
			sql = "SELECT * FROM `linked` WHERE `honorary` = FALSE AND `rank` >= 7 AND `sid` IN (SELECT `id` FROM `active`);"
			query = self.db.query(sql)
			if len(query) == 0:
				await self.no_admin()
			asyncio.sleep(1800)
	async def no_admin(self):
		ch=self.getchannel("admin")
		last=False
		notify="<@&{}> There's no admin on shift!".format(Settings.Ranks[Settings.Admin["rank"]][0])
		notify="There's no admin on shift!"
		async for msg in self.client.logs_from(ch,limit=1):
			if msg.author == self.client.user and msg.content == notify:
				last=True
		if not last:
			self.run(self.send(ch,notify))
