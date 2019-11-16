import os
from os.path import isfile, getsize
import sqlite3

allowedTimeSlots = ("antes del desayuno","despues del desayuno","antes del almuerzo","despues del almuerzo",
                    "antes de la merienda","despues de la merienda","antes de la cena","despues de la cena")

user_fields = ("UserID","name","hashed_password","public_id","isAdmin")

def dict_factory(cursor, row):
	    d = {}
	    for idx, col in enumerate(cursor.description):
	        d[col[0]] = row[idx]
	    return d

class GlucoseDB():
	def __init__(self,filename):
		self.filename = filename

	def freshMeasurementsDB(self):
		newDB = sqlite3.connect(self.filename)
		cursor = newDB.cursor()

		cursor.execute("CREATE TABLE users(UserID INTEGER PRIMARY KEY, name TEXT, hashed_password TEXT, public_id TEXT, isAdmin BOOLEAN)")
		newDB.commit()

		cursor.execute("CREATE TABLE measurements(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(UserID), value INTEGER, timeSlot TEXT, date TIMESTAMP, carbs INTEGER, food_insuline INTEGER, correction_insuline INTEGER)")
		newDB.commit()

		#Add a dummy user: admin, password: admin
		self.add_new_user("admin","4e6883d3-f023-4998-a9c9-5b7f3ff4d4a4","sha256$zJPN0jvy$50b13f42e41b6613345328647b52a122d334b143542f719b43b3d59ab408f42d",True)	    
		return newDB


	def getDBConnection(self):

		filename = self.filename

		if not isfile(filename):
			return self.freshMeasurementsDB()
		if getsize(filename) >= 100: # SQLite database file header is 100 bytes
			with open(filename, 'rb') as fd: header = fd.read(100)

	    	if header[:16] == 'SQLite format 3\x00':
	    		# is a valid db file
	    		return sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)

		os.rename(filename,'backup-{}.db'.format(dt.datetime.now()))
		return self.freshMeasurementsDB()

#---------- Measurement related queries -------------------------

	def insert_measure(self,user_id,timeSlot,date,value=0,carbs=0,correction_insuline=0,food_insuline=0):
		new_measure = {
			'value': value,
			'timeSlot': timeSlot,
			'date': date,
			'user_id': user_id,
			'carbs': carbs,
			'correction_insuline': correction_insuline,
			'food_insuline' : food_insuline
		}

		conn = self.getDBConnection()
		conn.row_factory = dict_factory
		cur = conn.cursor()
		cur.execute('''INSERT INTO measurements(value, timeslot, date,user_id,carbs,correction_insuline,food_insuline)
					VALUES(:value,:timeSlot,:date, :user_id, :carbs, :correction_insuline, :food_insuline)''', new_measure)
		conn.commit()
		conn.close()


	def get_measurements(self,user_id,starting_date,end_date,ordered=False):
	    query = "SELECT * FROM measurements WHERE user_id = {} AND date BETWEEN".format(user_id)
	    to_filter = []    

	    query += ' ? AND'
	    to_filter.append(starting_date)
	    query += ' ?'
	    to_filter.append(end_date)
	    if ordered:
	        query += ' ORDER BY date ASC'
	    query += ';'

	    conn = self.getDBConnection()
	    conn.row_factory = dict_factory
	    cur = conn.cursor()

	    results = cur.execute(query, to_filter).fetchall()

	    conn.close()

	    return results

	def get_all_measures(self,user_id):
		#Todo devolver solo los correspondientes al usuario
		conn = self.getDBConnection()
		conn.row_factory = dict_factory
		cur = conn.cursor()
		query = "SELECT * FROM measurements WHERE user_id={};".format(user_id)
		all_measures = cur.execute(query).fetchall()

		conn.close()
		return all_measures

	def get_measurement_with_id(self,id):
		#id must be an integer (curated value)
		query = "SELECT * FROM measurements WHERE id={};".format(id)

		conn = self.getDBConnection()
		conn.row_factory = dict_factory
		cur = conn.cursor()
		results = cur.execute(query).fetchall()
		conn.close()

		return results


	def delete_measure(self,id):
		query = "DELETE FROM measurements WHERE id={};".format(id)

		conn = self.getDBConnection()
		conn.row_factory = dict_factory
		cur = conn.cursor()
		results = cur.execute(query)
		conn.commit()
		conn.close()


# ----------- Users table -------------------------------------------------

	def add_new_user(self,username,public_id,hashed_password,isAdmin):
		conn = self.getDBConnection()
		conn.row_factory = dict_factory
		cur = conn.cursor()

		new_user = {
			'name': username,
			'public_id':public_id,
			'hashed_password':hashed_password,
			'isAdmin':isAdmin
		}

		cur.execute('''INSERT INTO users(name, public_id,hashed_password,isAdmin)
	                  VALUES(:name,:public_id,:hashed_password,:isAdmin)''', new_user)
		conn.commit()
		conn.close()

	def get_user_with_name(self,aSearchedUsername):
		#Check if user exists without passing it to the DB controler (prevent injection)
		#To do: la bd es chica, investigar como hacerlo para que escale 
	    users = self.get_all_users()

	    user_info = next( (user for user in users if user['name'] == aSearchedUsername), None)

	    return user_info

	def get_user_by_public_id(self,aPublicId):

		users = self.get_all_users()

		user_info = next( (user for user in users if user['public_id'] == aPublicId), None)

		return user_info

	def get_all_users(self):
		conn = self.getDBConnection()
		conn.row_factory = dict_factory
		cur = conn.cursor()
		all_users = cur.execute('SELECT * FROM users;').fetchall()

		conn.close()
		return all_users


	def update_user(self,id,update_data):

		for field in update_data:
			if field in user_fields:
				if isinstance(update_data[field], basestring):
					value = update_data[field]
				else:
					value = int(update_data[field])

				query = "UPDATE users SET {} = {} WHERE UserID = {};".format(field,value,id)
				run_query(self,query)

	def delete_user(self,id):
		query = "DELETE FROM users WHERE UserID={};".format(id)
		run_query(self,query)
		
#########################################################################

def run_query(db,query):
	conn = db.getDBConnection()
	conn.row_factory = dict_factory
	cur = conn.cursor()
	results = cur.execute(query)
	conn.commit()
	conn.close()
	return results