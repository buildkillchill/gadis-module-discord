import datetime
import asyncio
import discord
import logging
import random
import time
import os

import common

from settings import Settings

class Module(common.BaseModule):
	__name__ = "Rank Manager"
	__version__ = "3.07"
	def __init__(self, enabled, db, client=None):
		common.BaseModule.__init__(self, enabled, db, client)
		self.addcmd("apply", self.apply, "Apply for admin")
		self.addcmd("applicants", self.applicants, "View list of admin applicants.", rank=Settings.Admin["rank"], private=True)
		self.addcmd("letters", self.letters, "View the admin's letters of recommendation or disapproval of applicants", rank=Settings.OwnerRank, private=True)
		self.addcmd("approveid", self.approve, "Approve application", rank=Settings.OwnerRank)
		self.addcmd("striprank", self.strip, "Strip user of rank and title", rank=Settings.OwnerRank)
		self.addcmd("retire", self.retire, "Step down from your position", rank=Settings.Admin["rank"])
		self.addcmd("stepdown", self.retire, "Step down from your position", rank=Settings.Admin["rank"])
		self.addcmd("demote", self.demote, "Demote person", rank=Settings.OwnerRank)
		self.addcmd("updateranks", self.update, "Force update ranks", rank=Settings.OwnerRank)
		self.addcmd("testsetrank", self.testsr, "Test User.setrank", rank=Settings.OwnerRank)
		client.loop.create_task(self.auto_update())
	def char_fix(self, s):
		return s.encode('ascii', 'ignore').decode('ascii')
	async def testsr(self, args, pmsg):
		self.logger.debug("BEGIN TEST: User.setrank")
		user = common.User.from_discord_id(self.client, self.db, pmsg.mentions[0].id)
		rank = user.rank()
		prev = user.previous_rank()
		t = int(time.time())
		await self.send(pmsg.channel, "Setting {}'s rank to {} at {}".format(pmsg.mentions[0].mention, prev, t))
		await user.setrank(prev, "You are being subjected to a test. Your rank will be restored, so do not panic.", False)
		await self.send(pmsg.channel, "Done. Took {}s".format(int(time.time())-t))
		t = int(time.time())
		await self.send(pmsg.channel, "Sleeping for 10 seconds")
		await asyncio.sleep(10)
		await self.send(pmsg.channel, "Restoring {}'s rank to {} at {}".format(pmsg.mentions[0].mention, rank, t))
		await user.setrank(rank)
		await self.send(pmsg.channel, "Done. Took {}s".format(int(time.time())-t))
		self.logger.debug("TEST COMPLETED: User.setrank ({}s)".format(int(time.time())-t))
	async def update(self, args=None, pmsg=None):
		self.logger.info("Checking for rank updates...")
		t = int(time.time())
		server = common.getserver(self.client)
		for member in server.members:
			roles = common.getroles(self.client, self.db, common.getrank(self.db, member.id))
			user = common.User.from_discord_id(self.client, self.db, member.id)
			if user == None: continue
			donor = discord.utils.get(common.getserver(self.client).roles, name="Donator")
			donated_query_res = user.donated()
			prev_roles = common.getroles(self.client, self.db, user.previous_rank())
			if donor in prev_roles and donated_query_res == 0:
				prev_roles.remove(donor)
			if len(roles) == 0 or len(user.roles()) == 0:
				continue
			if not len(prev_roles) == 0:
				await self.client.add_roles(member, *prev_roles)
			if donor in roles and not donor in member.roles and donated_query_res == 1:
				await self.send(self.getchannel("general"), "Thank you, {}, for donating. It's donations, like yours, that keep this server running.".format(member.mention))
			for role in roles:
				if role in member.roles: continue
				self.logger.info("Ranks are out of date for member with ID {}".format(member.id))
				if role == donor:
					if donated_query_res == 0:
						roles.remove(role)
						self.logger.info("Member {} exceeds Donator rank but hasn't donated, not giving donator...".format(member.id))
					continue
				if user.rank() == 1: continue
				await self.send(self.getchannel("general"), "Congratulations on making {}, {}!".format(role.name, member.mention))
			await self.client.add_roles(member, *roles)
			await asyncio.sleep(0.25)
			if donor in member.roles and donated_query_res == 0:
				await self.client.remove_roles(member, donor)
				self.logger.info("Member {} exceeds Donator rank but hasn't donated, revoking...".format(member.id))
			await asyncio.sleep(0.25)
		self.logger.info("Finished checking for rank updates after {}s".format(int(time.time())-t))
	async def auto_update(self):
		while True:
			try:
				await self.update()
			except Exception as e:
				self.logger.error("Unhandled exception in update(), attempting to log to error log...")
				try:
					with open("/var/log/gadis/error.log", 'a') as f:
						f.write(str(e))
				except Exception:
					try:
						with open(os.path.expanduser("~/.gadis/log/error.log"), 'a') as f:
							f.write(str(e))
					except Exception:
						self.logger.error("Could not log error.")
			dt = datetime.datetime.now()
			await asyncio.sleep((60-dt.minute)*60)
	async def tick_down(self, channel, seconds, message):
		msg = await self.send(channel, message.format(time))
		remains = seconds
		while remains > 0:
			await asyncio.sleep(1)
			remains = remains - 1
			await self.edit(msg, message.format(remains))
	async def retire(self, args, pmsg):
		self.logger.info("WARNING: RETIREMENT PROCESS STARTED FOR MEMBER WITH ID {}".format(pmsg.author.id))
		admin = common.User.from_discord_id(self.client, self.db, pmsg.author.id)
		self.client.loop.create_task(self.tick_down(pmsg.channel, 60, "{} are you sure you want to retire? You will have to go through the whole application process again if you want your position back. You have {{}} seconds to reply with _EXACTLY_ `I HEREBY FORFEIT MY POSITION AND GO INTO RETIREMENT`. This is case sensitive.".format(pmsg.author.mention)))
		reply = (await self.getreply(60, pmsg.author, pmsg.channel)).content
		if reply == "I HEREBY FORFEIT MY POSITION AND GO INTO RETIREMENT":
			await admin.setrank(admin.previous_rank(), "Thank you for your service. We're sorry to see you have chosen to step down.", False)
			self.logger.info("Member with ID {} has chosen to retire.".format(pmsg.author.id))
		else:
			await self.send(pmsg.channel, "Glad to see you reconsidered, {}. Thank you for your ongoing service!".format(pmsg.author.mention))
			self.logger.info("Member with ID {} has not completed the retirement confirmation or has changed their mind".format(pmsg.author.id))
	async def demote(self, args, pmsg):
		reason = ""
		lock = False
		if args[1].lower() == "lock":
			lock = True
			reason = common.strip_mentions(" ".join(args[2:]))
		else:
			reason = common.strip_mentions(" ".join(args[1:]))
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
		reply = (await self.getreply(60, pmsg.author, pmsg.channel)).content
		if reply.lower() == "y" or reply.lower() == "yes":
			msg = await self.send(pmsg.channel, "Plugging potato into battery terminals...")
			for m in pmsg.mentions:
				p = common.User.from_discord_id(self.client, self.db, m.id)
				await self.edit(msg, "Demoting {}".format(m.mention))
				await p.setrank(p.previous_rank(), reason, lock)
			await self.edit(msg, "Demotion complete.")
	async def approve(self, args, pmsg):
		applicant = common.User.from_discord_id(self.client, self.db, args[1])
		if IsApplicant(self.db, applicant.ID()):
			self.db.run("UPDATE `applications` SET `accepted`=TRUE WHERE `id`={}".format(applicant.ID()))
			last = await self.send(pmsg.author, "Setting Rank...")
			await applicant.setrank(Settings.Admin["rank"])
			await self.edit(last, "Cleaning up...")
			self.db.run("DELETE FROM `recommends` WHERE `id`={}".format(applicant.ID()))
		else:
			await self.send(pmsg.author, "They are not an applicant. Please have them apply first.")
	async def strip(self, args, pmsg):
		user = common.User.from_discord_id(self.client, self.db, args[1])
		self.StripRank(user)
		await self.send(pmsg.author, "Rank and title has been hereby stripped from {}".format(user.discord().mention))
	async def StripRank(self, user):
		self.logger.info("Stripping rank from {}".format(user.id["did"]))
		await self.send(user.discord(), "You are hereby stripped of all rank and title.")
		await user.setrank(1)
		member = common.getmember(self.client, user)
		for role in member.roles:
			if str(role) != "everyone" and str(role) != "@everyone":
				await self.client.remove_role(member, role)
		common.runrcon("ulx removeuserid {}".format(user.steamID()))
	async def apply(self, args, pmsg):
		usr = common.User.from_discord_id(self.client, self.db, pmsg.author.id)
		taken = len(self.db.query("SELECT `id` FROM `accounts` WHERE `rank` >= {}".format(Settings.Admin["rank"])))
		appcount = len(self.db.query("SELECT * FROM `applications` WHERE `accepted`=FALSE AND `denied`=FALSE AND `interviewed`=FALSE"))
		if usr == None:
			await self.send(pmsg.channel, "Your account is not linked, please type `link` to begin.")
		if usr.rank() >= Settings.Admin["rank"]:
			await self.send(pmsg.channel, "Nice try, we don't accept applications for superadmin or developer.")
		elif not usr.locked():
			if Settings.Admin["positions"] <= taken or Settings.Admin["max_apps"] <= appcount:
				await self.send(pmsg.channel, "We are not currently accepting applications for admin.")
			else:
				linked = len(self.db.query("SELECT `id` FROM `accounts` WHERE `sid` IS NOT NULL AND `did`={}".format(pmsg.author.id)))
				if linked > 0:
					aid = int(pmsg.author.id)
					time=Settings.Admin["req_hours"]
					id=self.db.query("SELECT `id` FROM `accounts` WHERE `did`=%s AND `hours` >= %s", [aid,time])
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
				applicant = self.db.query("SELECT `did` FROM `accounts` WHERE `id`={}".format(recommendation[0]))
				applicant = await self.getuser(applicant[0][0])
				await self.edit(last, "Loading authoring admin's ID...")
				recommender = self.db.query("SELECT `did` FROM `accounts` WHERE `id`={}".format(recommendation[1]))
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
		rank = common.getrank(self.db, pmsg.author.id)
		await self.send(pmsg.author, "Welcome to The Applicants Module.\nOwner commands:```interview       Extend an interview invite\napprove         Approve application\ndeny            Deny application```Admin commands:```recommend       Recommend applicant for promotion.\ndisapprove      Recommend denial of application```Common commands:```next            Show next applicant\nstop            Exit The Applicant Module```")
		lastmsg = await self.send(pmsg.author, "Fetching applicants...")
		apps = self.db.query("SELECT `id`,`message` FROM `applications` WHERE `denied` = FALSE AND `accepted` = FALSE")
		await self.edit(lastmsg,"Randomizing order...")
		apps = sorted(apps,key=lambda k: random.random())
		if len(apps) > 0:
			await self.edit(lastmsg,"Stage 1 Complete.")
			azi = await self.client.get_user_info(str(Settings.People["owner"]))
			if azi.avatar_url == "":
				azi_icon = azi.default_icon_url
			else:
				azi_icon = azi.avatar_url
			for app in apps:
				await self.edit(lastmsg, "Getting applicant's Discord info...")
				iapp = common.User.from_id(self.client, self.db, app[0])
				iadm = common.User.from_discord_id(self.client, self.db, pmsg.author.id)
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
					elif subcmd == "approve" and rank >= Settings.OwnerRank:
						self.db.run("UPDATE `applications` SET `accepted`=TRUE WHERE `id`={}".format(app[0]))
						await self.edit(lastmsg, "Setting Rank...")
						await iapp.setrank(Settings.Admin["rank"])
						await self.edit(lastmsg, "Cleaning up...")
						self.db.run("DELETE FROM `recommends` WHERE `id`={}".format(app[0]))
					elif subcmd == "approve":
						err = True
						emsg = "Owner only command"
					elif subcmd == "deny" and rank >= 9:
						self.db.run("UPDATE `applications` SET `denied`=TRUE WHERE `id`=%s", [app[0]])
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
						await self.send(applicant, "You have been selected for an interview. Please DM <@{}> to proceed.".format(Settings.People["owner"]))
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
def IsApplicant(db, id):
	results = db.query("SELECT * FROM `applications` WHERE `id`={}".format(id))
	if len(results) > 0:
		return True
	else:
		return False
