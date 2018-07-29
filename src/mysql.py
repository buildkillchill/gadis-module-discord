import MySQLdb
import logging
import sys

from common import LoggerExtension
from warnings import filterwarnings
from settings import Settings

if not os.path.exists(os.path.expanduser("~/.gadis")):
	sys.path.append('/usr/local/share/gadis')
else
	sys.path.append(os.path.expanduser("~/.gadis/share/gadis"))

def default():
	return MySQLWrapper(Settings.MySQL["data"], Settings.MySQL["user"], Settings.MySQL["pass"], Settings.MySQL["host"], Settings.MySQL["port"])

class MySQLWrapper():
	def __init__(self, DATABASE, USER, PASS, HOST, PORT=3306):
		self.connection = MySQLdb.connect(db=DATABASE,host=HOST,port=PORT,user=USER,passwd=PASS)
		self.connection.autocommit(True)
		self.connection.ping(True)
		self.cursor = self.connection.cursor()
		logging.setLoggerClass(LoggerExtension)
		self.logger = logging.getLogger("GADIS.MYSQL")
		filterwarnings('ignore', category = MySQLdb.Warning)
	def query(self, sql, replacements=None):
		self.logger.debug("Executing '{}'".format(sql))
		if replacements == None:
			self.cursor.execute(sql)
		else:
			self.cursor.execute(sql,replacements)
		return self.cursor.fetchall()
	def run(self, sql, replacements=None):
		self.logger.debug("Executing '{}'".format(sql))
		if replacements == None:
			self.cursor.execute(sql)
		else:
			self.cursor.execute(sql,replacements)
	def disconnect(self):
		self.logger.extra("Closing DB connection")
		self.connection.close()
