import MySQLdb
from warnings import filterwarnings
from settings import Settings

def default():
	return MySQLWrapper(Settings.MySQL["Data"], Settings.MySQL["User"], Settings.MySQL["Pass"], Settings.MySQL["Host"], Settings.MySQL["Port"])

class MySQLWrapper():
	def __init__(self, DATABASE, USER, PASS, HOST, PORT=3306):
		self.connection = MySQLdb.connect(db=DATABASE,host=HOST,port=PORT,user=USER,passwd=PASS)
		self.connection.autocommit(True)
		self.connection.ping(True)
		self.cursor = self.connection.cursor()
		filterwarnings('ignore', category = MySQLdb.Warning)
	def query(self, sql, replacements=None):
		if replacements == None:
			self.cursor.execute(sql)
		else:
			self.cursor.execute(sql,replacements)
		return self.cursor.fetchall()
	def run(self, sql, replacements=None):
		if replacements == None:
			self.cursor.execute(sql)
		else:
			self.cursor.execute(sql,replacements)
	def disconnect(self):
		self.connection.close()