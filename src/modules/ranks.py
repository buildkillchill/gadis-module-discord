import datetime
import asyncio
import discord
import random
import valve
import valve.rcon

import common
import mysql

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Rank Manager"
	__version__ = "3.02"
	def __init__(self, enabled, client=None):
		common.BaseModule.__init__(self, enabled, client)
		self.addcmd("apply", self.apply, "Apply for admin")
		self.addcmd("applicants", self.applicants, "View list of admin applicants.", rank=7, private=True)
		self.addcmd("letters", self.letters, "View the admin's letters of recommendation or disapproval of applicants", rank=9, private=True)
		self.addcmd("approveid", self.approve, "Approve application", rank=10)
		self.addcmd("striprank", self.strip, "Strip user of rank and title", rank=10)
		self.addcmd("retire", self.retire, "Step down from your position", rank=8)
		self.addcmd("stepdown", self.retire, "Step down from your position", rank=8)
		self.addcmd("demote", self.demote, "Demote person", rank=10)
		self.addcmd("updateranks", self.update, "Force update ranks", rank=9)
		client.loop.create_task(self.auto_update())
	def char_fix(self, s):
		return s.encode('ascii', 'ignore').decode('ascii')
	async def update(self, args=None, pmsg=None):
		server = common.getserver(self.client)
		for member in server.members:
			roles = common.getroles(self.client, common.getrank(member.id))
			user = common.User.from_discord_id(self.client, member.id)
			if user == None: continue
			donor = discord.utils.get(common.getserver(self.client).roles, name="Donator")
			if len(roles) == 0 or len(user.role()) == 0:
				continue
			await self.client.add_roles(member, *common.getroles(self.client, user.previous_rank()))
			if donor in roles and not donor in member.roles:
				await self.send(self.getchannel("general"), "Thank you, {}, for donating. It's donations, like yours, that keep this server running.".format(member.id))
			for role in roles:
				if role == donor or role in member.roles: continue
				await self.send(self.getchannel("general"), "Congratulations on making {}, {}!".format(role.mention, member.mention))
			await self.client.add_roles(member, *roles)
	async def auto_update(self):
		while True:
			await self.update()
			dt = datetime.datetime.now()
			await asyncio.sleep((60-dt.minute)*60)
	async def tick_down(self, channel, seconds, message):
		msg = await self.send(channel, message.format(time))
		remains = seconds
		while remains > 0:
			asyncio.sleep(1)
			remains = remains - 1
			await self.edit(msg, message.format(remains))
	async def retire(self, args, pmsg):
		admin = common.User.from_discord_id(self.client, pmsg.author.id)
		self.client.create_task(self.tick_down(pmsg.channel, 60, "{} are you sure you want to retire? You will have to go through the whole application process again if you want your position back. You have \{\} seconds to reply with _EXACTLY_ `I HEREBY FORFEIT MY POSITION AND GO INTO RETIREMENT`. This is case sensitive.".format(pmsg.author.mention)))
		reply = await self.getreply(60, pmsg.author, pmsg.channel)
		if reply == "I HEREBY FORFEIT MY POSITION AND GO INTO RETIREMENT":
			admin.setrank(admin.previous_rank(), "Thank you for your service. We're sorry to see you have chosen to step down.", False)
		else:
			await self.send(pmsg.channel, "Glad to see you reconsidered, {}. Thank you for your ongoing service!".format(author.mention))
	async def demote(self, args, pmsg):
		reason = ""
		lock = False
		if args[1].lower() == "lock":
			lock = True
			for arg in args[2:]:
				if not re.match("(@.*#[0-9]{4}|\<@[0-9]+\>)", arg):
					reason = "{} {}".format(reason, arg)
		else:
			for arg in args[1:]:
				if not re.match("(@.*#[0-9]{4}|\<@[0-9]+\>)", arg):
					reason = "{} {}".format(reason, arg)
		text = "Are you sure you want to demote "
		first = True
		for m in pmsg.mentions:
			if first:
				first = False
				text = "{}{}".format(text, m.mention)
			else:
				text = "{}, {}".format(text, m.mention)
		text = "{}?".format(text)
		await self.send(pmsg.channel, text)
		reply = await self.getreply(60, pmsg.author, pmsg.channel)
		if reply.lower() == "y" or reply.lower() == "yes":
			msg = await self.send(pmsg.channel, "Plugging potato into battery terminals...")
			for m in pmsg.mentions:
				p = common.User.from_discord_id(self.client, pmsg.author.id)
				await self.edit(msg, "Demoting {}".format(m.mention))
				p.setrank(p.previous_rank(), reason, lock)
			await self.edit(msg, "Demotion complete.")
	async def approve(self, args, pmsg):
		applicant = common.User.from_discord_id(self.client, args[1])
		if IsApplicant(applicant.ID()):
			self.db.run("UPDATE `applications` SET `accepted`=True WHERE `id`={}".format(applicant.ID()))
			last = await self.send(pmsg.author, "Setting Rank...")
			await applicant.setrank(7)
			await self.edit(last, "Cleaning up...")
			self.db.run("DELETE FROM `recommends` WHERE `id`={}".format(applicant.ID()))
		else:
			await self.send(pmsg.author, "They are not an applicant. Please have them apply first.")
	async def strip(self, args, pmsg):
		user = common.User.from_discord_id(args[1])
		self.StripRank(user)
		await self.send(pmsg.author, "Rank and title has been hereby stripped from {}".format(user.discord().mention))
	async def StripRank(self, user):
		await self.send(user.discord(), "You are hereby stripped of all rank and title.")
		user.setrank(1)
		member = common.getmember(self.client, user)
		for role in member.roles:
			if str(role) != "everyone" and str(role) != "@everyone":
				await self.client.remove_role(member, role)
		valve.rcon.execute((Settings.RCON["host"], Settings.RCON["port"]), Settings.RCON["pass"], "ulx removeuserid {}".format(user.steamID()))
	async def apply(self, args, pmsg):
		usr = common.User.from_discord_id(self.client, pmsg.author.id)
		taken = len(self.db.query("SELECT `id` FROM `linked` WHERE `rank` >= 7"))
		appcount = len(self.db.query("SELECT * FROM `applications` WHERE `accepted`=FALSE AND `denied`=FALSE AND `interviewed`=FALSE"))
		if usr.rank() >= 7:
			await self.send(pmsg.channel, "Nice try, we don't accept applications for superadmin or developer.")
		elif not usr.locked():
			if Settings.Admin["positions"] <= taken or Settings.Admin["max_apps"] <= appcount:
				await self.send(pmsg.channel, "We are not currently accepting applications for admin.")
			else:
				linked = len(self.db.query("SELECT `id` FROM `linked` WHERE `sid` IS NOT NULL AND `did`={}".format(pmsg.author.id)))
				if linked > 0:
					aid = int(pmsg.author.id)
					time=Settings.Admin["req_hours"]
					id=self.db.query("SELECT `id` FROM `linked` WHERE `did`=%s AND `hours` >= %s", [aid,time])
					if len(id) > 0:
						id=int(id[0][0])
						if len(self.db.query("SELECT `id` FROM `applications` WHERE `id`=%s",[id])):
							await self.send(pmsg.channel, "You have already applied.")
						else:
							await self.send(pmsg.channel, "In 1000 characters or less, tell us why you are a good canidate. _Note: This application will autmatically cancel if you do not respond within 5 minutes. You may also type `cancel application` to manually cancel._")
							reason = await self.getreply(1200, pmsg.author, pmsg.channel)
						if reason == None or reason.content.lower() == "cancel application":
							await self.send(pmsg.channel, "Application cancelled.")
						else:
							self.db.run("INSERT INTO `applications` (`id`,`message`) VALUES (%s,%s) ON DUPLICATE KEY UPDATE `id`=%s",(id,reason.content,id))
							await self.send(pmsg.channel, "You have been added to the list of applicants. _This does not guarantee you will get the position._")
					else:
						await self.send(pmsg.channel, "We have determined that you are not eligible for admin at this time. If you believe this is a mistake, please ask Azi, Timberwolf, or Dark for clarification.")
				else:
					await self.send(pmsg.author, "Before you can apply for admin, you must link you account. You may do so here: http://bkcservice.zenforic.com/link/?did={}".format(pmsg.author.id))
		else:
			await self.send(pmsg.channel, "Your account was locked from applying.")
	async def letters(self, args, pmsg):
		await self.send(pmsg.author, "Welcome to the Letter Submodule. To go to the next letter, send `next`. To cancel viewing, type `cancel` or `stop`.")
		last = await self.send(pmsg.author, "Fetching letters...")
		list = self.db.query("SELECT * FROM `recommends` ORDER BY `id`")
		if len(list) > 0:
			for recommendation in list:
				await self.edit(last, "Found letter. Loading applicant ID...")
				applicant = self.db.query("SELECT `did` FROM `linked` WHERE `id`={}".format(recommendation[0]))
				applicant = await self.getuser(applicant[0][0])
				await self.edit(last, "Loading authoring admin's ID...")
				recommender = self.db.query("SELECT `did` FROM `linked` WHERE `id`={}".format(recommendation[1]))
				recommender = await self.getuser(recommender[0][0])
				await self.edit(last, "Checking letter type...")
				recommends = recommendation[3]
				if recommends:
					title="Recommendation"
				else:
					title="Disapproval"
				title = "Letter of {} for {}".format(title, applicant.name)
				embed = discord.Embed(title=title,description=recommendation[2])
				embed.set_author(name=recommender.name, icon_url=recommender.avatar_url)
				await self.edit(last, applicant.mention)
				await self.edit_embed(last, embed)
				while True:
					reply = await self.getreply(60, pmsg.author, pmsg.channel)
					if reply != None and reply.content.lower() in ["cancel","stop"]:
						return
					elif reply != None and reply.content.lower() == "next":
						break
			await self.send(pmsg.author, "No more letters to display or was cancelled.")
		else:
			await self.edit(last, "No letters to display.")

	async def applicants(self, args, pmsg):
		rank = self.getrank(pmsg.author.id)
		await self.send(pmsg.author, "Welcome to The Applicants Module.\nOwner commands:```interview       Extend an interview invite\napprove         Approve application\ndeny            Deny application```Admin commands:```recommend       Recommend applicant for promotion.\ndisapprove      Recommend denial of application```Common commands:```next            Show next applicant\nstop            Exit The Applicant Module```")
		lastmsg = await self.send(pmsg.author, "Fetching applicants...")
		apps = self.db.query("SELECT `id`,`message` FROM `applications` WHERE `denied` = FALSE AND `accepted` = FALSE")
		await self.edit(lastmsg,"Randomizing order...")
		apps = sorted(apps,key=lambda k: random.random())
		if len(apps) > 0:
			await self.edit(lastmsg,"Stage 1 Complete.")
			azi = await self.client.get_user_info('185447502655258626')
			if azi.avatar_url == "":
				azi_icon = azi.default_icon_url
			else:
				azi_icon = azi.avatar_url
			for app in apps:
				await self.edit(lastmsg, "Getting applicant's Discord info...")
				iapp = common.User.from_id(self.client, app[0])
				iadm = common.User.from_discord_id(self.client, pmsg.author.id)
				id = iapp.ID()
				aid = iadm.ID()
				applicant = await iapp.discord()
				if applicant.avatar_url == "":
					app_icon = applicant.default_avatar_url
				else:
					app_icon = applicant.avatar_url
				appem=discord.Embed(title="Application for Promotion", description=app[1])
				appem.set_author(name=applicant.name, icon_url=app_icon)
				await self.edit(lastmsg, "Applicant:")
				await self.edit_embed(lastmsg, appem)

				cont = await self.getreply(120, pmsg.author, pmsg.channel)
				err = False
				if cont != None:
					subcmd=cont.content.lower()
					if subcmd == "stop":
						break
					elif subcmd == "next":
						continue
					elif subcmd == "recommend":
						await self.send(pmsg.author, "Please write a letter of recommendation. You have 20 minutes to write _up to_ 1000 characters.")
						msg = await self.getreply(1200, pmsg.author, pmsg.channel)
						if msg == None and msg.content.lower() == "cancel":
							break
						self.db.run("INSERT INTO `recommends` (`id`,`admin`,`reason`,`positive`) VALUES (%s, %s, %s, TRUE) ON DUPLICATE KEY UPDATE `reason`=%s",(app[0], aid, msg.content, msg.content))
						await self.send(pmsg.author, "Your recommendation has been submitted.")
					elif subcmd == "disapprove":
						await self.send(pmsg.author, "Please write a letter of disapproval. You have 20 minutes to write _up to_ 1000 characters.")
						msg = await self.getreply(1200, pmsg.author, pmsg.channel)
						if msg == None and msg.content.lower() == "cancel":
							break
						self.db.run("INSERT INTO `recommends` (`id`,`admin`,`reason`,`positive`) VALUES (%s, %s, %s, FALSE) ON DUPLICATE KEY UPDATE `reason`=%s",(app[0], aid, msg.content, msg.content))
						await self.send(pmsg.author, "Your disrecommendation has been submitted.")
					elif subcmd == "approve" and rank == 10:
						await self.edit(lastmsg, "Setting Rank...")
						await iapp.setrank(7)
						await self.edit(lastmsg, "Done.")
					elif subcmd == "approve":
						err = True
						emsg = "Owner only command"
					elif subcmd == "deny" and rank >= 9:
						self.db.run("UPDATE `applications` SET `denied`=True WHERE `id`=%s", [app[0]])
						await self.send(pmsg.author,"{} has been denied. What should the letter of denial contain? _Type `n` or `no` to silently deny. Waiting 5 minutes will also silently deny._".format(applicant.mention))
						cont = await self.getreply(300, pmsg.author, pmsg.channel)
						if cont == None or cont.content.lower() == "no" or cont.content.lower() == "n":
							await self.send(pmsg.author, ":fire: Silently dismissing application...")
						else:
							await self.send(applicant, "You application for admin has been **DENIED**.")
							letter=discord.Embed(title='Letter of Denial', description=cont.content)
							letter.set_author(name="Azicus", icon_url=azi_icon)
							await self.send_embed(applicant, letter)
						self.db.run("DELETE FROM `recommends` WHERE `id`={}".format(app[0]))
					elif subcmd == "deny":
						err = True
						emsg = "Owner only command"
					elif subcmd == "interview" and rank >= 9:
						await self.send(applicant, "You have been selected for an interview. Please DM <@185447502655258626> to proceed.")
						await self.send(pmsg.author, "I sent {} an interview invitation.\nDo you wish to continue looking though applicants?".format(applicant.mention))
						self.db.run("UPDATE `applications` SET `interviewed`=TRUE WHERE `id`={}".format(app[0]))
						cont = await self.getreply(60, pmsg.author, pmsg.channel)
						if cont == None or cont.content.lower() == "no" or cont.content.lower() == "n":
							break
					elif subcmd == "interview":
						err = True
						emsg = "Owner only command"
					else:
						err = True
						emsg = "Invalid command"
					if err:
						await self.edit(lastmsg, "Command Failed.")
						errem = discord.Embed(title="Error:",description=emsg)
						errem.set_author(name="BKC Services", icon_url=self.client.user.avatar_url)
						await self.edit_embed(lastmsg, errem)
						return
			await self.send(pmsg.author, "No more applicants remain.")
		else:
			await self.edit(lastmsg, "No viable applicants found.")
def IsApplicant(id):
	db = mysql.default()
	results = db.query("SELECT * FROM `applications` WHERE `id`={}".format(id))
	if len(results) > 0:
		return True
	else:
		return False
