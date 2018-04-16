import MySQLdb
import logging
from warnings import filterwarnings
from settings import Settings

def default():
	return MySQLWrapper(Settings.MySQL["data"], Settings.MySQL["user"], Settings.MySQL["pass"], Settings.MySQL["host"], Settings.MySQL["port"])

class MySQLWrapper():
	def __init__(self, DATABASE, USER, PASS, HOST, PORT=3306):
		self.connection = MySQLdb.connect(db=DATABASE,host=HOST,port=PORT,user=USER,passwd=PASS)
		self.connection.autocommit(True)
		self.connection.ping(True)
		self.cursor = self.connection.cursor()
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
		self.logger.info("Closing DB connection")
		self.connection.close()
