import os

import datetime as dt

import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.code import Code

from collections import OrderedDict

import sys

def generate_measurement_output(aMeasure,user_id):
	aNewMeasure = {}
	for field in aMeasure:
		aNewMeasure[field] = aMeasure[field]
	aNewMeasure['id'] = "%i" % int(str(aMeasure['id']),16)
	aNewMeasure['user_id'] = "%i" % user_id
	return aNewMeasure

def createMeasurementsByUserCollection(db):
	collist = db.list_collection_names()
	#db.measurementsByUser.drop()
	if not "measurementsByUser" in collist:
  		db.create_collection("measurementsByUser")

		vexpr = {"$jsonSchema": {
		         "bsonType": "object",
		         "required": [ "name", "hashed_password", "public_id", "isAdmin", "measurements" ],
		         "properties": {
		         	"UserID": {
		         		"bsonType": "objectId"
		         	},
		            "name": {
		               "bsonType": "string",
		               "description": "must be a string and is required"
		            },
		            "hashed_password": {
		               "bsonType": "string",
		               "description": "must be a string and is required"
		            },
		            "public_id": {
		               "bsonType": "string",
		               "description": "must be a string and is required"
		            },
		            "isAdmin": {
		            	"bsonType": "bool",
		            	"description": "must be a boolean and is required"	
		            },
		            "measurements": {
		            	"bsonType": "array",
		            	"items": {
			            	"bsonType": "object",
			            	"required": [ "id", "timeSlot", "date" ],
			            	"properties": {
			            		"id": {
			            			"bsonType": "objectId"
			            		},
			            		"timeSlot": {
			            			"enum": [ "antes del desayuno","despues del desayuno","antes del almuerzo","despues del almuerzo",
		                    "antes de la merienda","despues de la merienda","antes de la cena","despues de la cena" ],
		            				"description": "can only be one of the enum values"
			            		},
			            		"date": {
			            			"bsonType": "date"
			            		},
			            		"value": {
			            			"bsonType": "int"
			            		},
			            		"carbs": {
			            			"bsonType": "int"
			            		},
			            		"food_insuline": {
			            			"bsonType": "int"
			            		},
			            		"correction_insuline": {
			            			"bsonType": "int"
			            		}
			            	}
			            }
		            }
		        }
				}
		}

		query = [('collMod', 'measurementsByUser'),
	        ('validator', vexpr),
	        ('validationLevel', 'moderate')]
		query = OrderedDict(query)
		db.command(query)


class GlucoseDB():
	def __init__(self,filename):
		self.filename = filename
		self.client = pymongo.MongoClient("mongodb://localhost:27017/")
		self.db = self.client[filename]

		createMeasurementsByUserCollection(self.db)

		self.measurementsByUser = self.db["measurementsByUser"]
		if self.measurementsByUser.count() == 0:
			self.add_new_user("admin","4e6883d3-f023-4998-a9c9-5b7f3ff4d4a4","sha256$zJPN0jvy$50b13f42e41b6613345328647b52a122d334b143542f719b43b3d59ab408f42d",True)	    

	

#---------- Measurement related queries -------------------------

	def insert_measure(self,user_id,timeSlot,date,value=0,carbs=0,correction_insuline=0,food_insuline=0):
		UserID = ObjectId( "%x" % user_id)
		new_measure = {
			'value': value,
			'timeSlot': timeSlot,
			'date': date,
			'carbs': carbs,
			'correction_insuline': correction_insuline,
			'food_insuline' : food_insuline,
			'id': ObjectId.from_datetime(date)
		}

		self.measurementsByUser.update({"_id": UserID},{"$push":{"measurements":new_measure}})

######### FIX get and delete #########################
	def get_measurements(self,user_id,starting_date,end_date,ordered=False):
		UserID = ObjectId( "%x" % user_id) #Convierto el numero de id a hex y genero el ObjectId
		#self.measurementsByUser.find("measurements": {"$elemMatch": {"$gte": starting_date, "$lte":end_date}})
		measures = next(self.measurementsByUser.aggregate([{"$match": {"_id": UserID} } ,
												{"$project": {"measurements" : {"$filter" : {"input": "$measurements",
																							"as": "measure",
																							"cond":{
																				                "$and" : [
																				                   { "$gte" : [ "$$measure.date", starting_date ] },
																				                   { "$lte" : [ "$$measure.date", end_date ] }
																				                ]
																				             } 
																				            }
																				}
															}
												}
											])
		)['measurements']
		if ordered:
			measures = sorted(measures, key = lambda i: i['date'])	
		results = []
		for aMeasure in measures:
			aNewMeasure = generate_measurement_output(aMeasure,user_id)
			results.append(aNewMeasure)
		return results

	def get_all_measures(self,user_id):
		UserID = ObjectId( "%x" % user_id) #Convierto el numero de id a hex y genero el ObjectId
		measurements = self.measurementsByUser.find_one({"_id":UserID})['measurements']
		results = []
		for aMeasure in measurements:
			aNewMeasure = generate_measurement_output(aMeasure,user_id)
			results.append(aNewMeasure)
		return results

	def get_measurement_with_id(self,id):
		aMeasureId = ObjectId( "%x" % id)
		result = self.measurementsByUser.find_one({"measurements.id":aMeasureId},{"measurements.$":1})
		if result:
			aMeasure = result['measurements'][0]
			user_id = int(str(result['_id']),16)
			return generate_measurement_output(aMeasure,user_id)

	def delete_measurement(self,id):
		aMeasureId = ObjectId( "%x" % id)
		#Ver si es necesario tomar por parametro eliddelusuariopara agilizar la busqueda
		#controler.measurementsByUser.update({"UserID":<user id>},{"$pull" : {"measurements" : {"id":id2}}})
		self.measurementsByUser.update({},{"$pull" : {"measurements" : {"id":aMeasureId}}})


# ----------- User  queries  -------------------------------------------------

	def add_new_user(self,username,public_id,hashed_password,isAdmin):
		new_user = {
			'name': username,
			'public_id':public_id,
			'hashed_password':hashed_password,
			'isAdmin': isAdmin,
			'measurements': []
		}

		self.measurementsByUser.insert_one(new_user)

	def get_user_by_id(self,aUserId):
		UserID = ObjectId( "%x" % aUserId) #Cnvierto el numero de id a hex y genero el ObjectId
		doc = (self.measurementsByUser.find_one({"_id":UserID}))
		user = {}
		if doc:
			user = {
					'name': doc['name'],
					'public_id':doc['public_id'],
					'hashed_password':doc['hashed_password'],
					'isAdmin': doc['isAdmin'],
					'UserID': "%i" % aUserId
			}
		return user

	def get_user_with_name(self,aSearchedUsername):
		doc = (self.measurementsByUser.find_one({"name":aSearchedUsername}))
		user = {}
		if doc:
			user = {
					'name': doc['name'],
					'public_id':doc['public_id'],
					'hashed_password':doc['hashed_password'],
					'isAdmin': doc['isAdmin'],
					'UserID': "%i" % int(str(doc['_id']),16)
			}
		return user

	def get_user_by_public_id(self,aPublicId):
		doc = (self.measurementsByUser.find_one({"public_id":aPublicId}))
		user = {}
		if doc:
			user = {
					'name': doc['name'],
					'public_id':doc['public_id'],
					'hashed_password':doc['hashed_password'],
					'isAdmin': doc['isAdmin'],
					'UserID': "%i" % int(str(doc['_id']),16)
			}
		return user

	def get_all_users(self):
		users = []
		for doc in self.measurementsByUser.find():
			user = {
				'name': doc['name'],
				'public_id':doc['public_id'],
				'hashed_password':doc['hashed_password'],
				'isAdmin': doc['isAdmin'],
				'UserID': "%i" % int(str(doc['_id']),16)
			}
			users.append(user)
		#[user for user in self.measurementsByUser.find()]
		return users


	def update_user(self,aUserId,update_data):
		UserID = ObjectId( "%x" % aUserId) #Cnvierto el numero de id a hex y genero el ObjectId
		self.measurementsByUser.update_one({"_id":UserID},{"$set":update_data})

	def delete_user(self,aUserId):
		UserID = ObjectId( "%x" % aUserId) #Cnvierto el numero de id a hex y genero el ObjectId
		self.measurementsByUser.delete_one({"_id":UserID})
		
#########################################################################


if __name__ == '__main__':
	db = GlucoseDB('Measurements')
	user_id = ObjectId('{}'.format("%x"%28982566204484353434896481831))
	date = dt.datetime.today()
	new_measure = {
		'value': 192,
		'timeSlot': "antes del desayuno",
		'date': date,
		'carbs': 0,
		'correction_insuline': 0,
		'food_insuline' : 0,
		'id': ObjectId.from_datetime(date)
	}

	db.measurementsByUser.update({"_id": user_id},{"$push":{"measurements":new_measure}})

	print db.measurementsByUser.find_one({"_id":user_id})['measurements']
	print list(db.measurementsByUser.find())

