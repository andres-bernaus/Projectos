import flask
from flask import request, jsonify, send_file, make_response

import datetime as dt
from dateutil.relativedelta import relativedelta

import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from functools import wraps

import string

from Measurement_table import Measurement_table
#from GlucoseSQL_controller import GlucoseDB
from GlucoseMongoDB_controller import GlucoseDB

import os
from os.path import isfile, getsize

app = flask.Flask(__name__)

app.config['SECRET_KEY'] = "SSIV-33"

allowedTimeSlots = ("antes del desayuno","despues del desayuno","antes del almuerzo","despues del almuerzo",
                    "antes de la merienda","despues de la merienda","antes de la cena","despues de la cena")


#db = GlucoseDB('measurements.db')
db = GlucoseDB('Measurements')

def modify_measure(new_measure):
    #To do
    return page_not_found(404)

def invalidTimeSlot(timeSlot):
    timeSlot = string.lower(timeSlot)
    return not (timeSlot in allowedTimeSlots)

#Decorator to manage token autenthication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])

        except Exception as e:
            return jsonify({'message' : 'Token is invalid! {}'.format(e)}), 401

        #If token is valid then exists user with that token's public_id
        current_user = db.get_user_by_public_id(data['public_id'])    
        return f(current_user, *args, **kwargs)

    return decorated

# -----------------------------------------------------------------------------

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Distant Reading Archive</h1>
<p>A prototype API for bloodsugar control.</p>
<h1>Current services:</h1>
<h2>- /api/v1/resources/measures/all</h2> <p>Displays all entries</p>
<h2>- /api/v1/resources/measures/between</h2> <p>Displays entries between dates: <b>start</b> and <b>end</b></p>'''

@app.route('/testconection', methods=['GET','POST','DELETE'])
def conection_test():
    return jsonify({'message':"ok"}),200


# ------------- User related paths --------------------------------------------

@app.route('/login')
def user_login():
    authorization = request.authorization
    
    #Check if user send username and password
    if not authorization or not authorization.username or not authorization.password:
        return make_response("Could not verify",401,{'WWW-Authenticate' : 'Basic realm="Login required"'})

    #Search username in the database
    user_info = db.get_user_with_name(authorization.username)

    #Verify password
    if not user_info:
        return make_response("Could not verify",401,{'WWW-Authenticate' : 'Username not found'})

    if check_password_hash(user_info['hashed_password'],authorization.password):
        #Generamos el token
        token = jwt.encode({'public_id': user_info['public_id'], 'exp': dt.datetime.utcnow() + dt.timedelta(days=1)}, app.config['SECRET_KEY'])
        return jsonify({'token' : token.decode('UTF-8')})
    
    return make_response("Could not verify",401,{'WWW-Authenticate' : 'Invalid password'})



@app.route('/api/v1/users/all', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user['isAdmin']:
        return jsonify({'message' : 'Cannot perform that function!'}),403
    return jsonify(db.get_all_users()),200



@app.route('/api/v1/users', methods=['GET','DELETE'])
@token_required
def get_or_delete_user(current_user):
    if not current_user['isAdmin']:
        return jsonify({'message' : 'Cannot perform that function!'}),403

    query_parameters = request.args

    id = query_parameters.get('id')

    if not id:
        return page_not_found(404)

    try:
        id = int(id)
    except ValueError:
        return jsonify({'message':"'id' must be an integer"}),400

    if request.method == 'GET':
        return jsonify(db.get_user_by_id(id)),200
    if request.method == 'DELETE':
        db.delete_user(id)
        return jsonify({'message':"User with id={} deleted".format(id)}), 200



@app.route('/api/v1/users', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user['isAdmin']:
        return jsonify({'message' : 'Cannot perform that function!'}),403

    required_fields = ("user","password")
    if not request.json or not all (f in request.json for f in required_fields):
        return jsonify({'message' : "Must provide json including 'user', and 'password'"}),400

    hashed_password = generate_password_hash(request.json['password'], method='sha256')

    #Check if username already exists
    if db.get_user_with_name(request.json['user']):
        return jsonify({'message' : "Username already in use"}),400

    db.add_new_user(request.json['user'],str(uuid.uuid4()),hashed_password,False)

    return jsonify({'message' : 'New user created!'}),201



@app.route('/api/v1/users/promote', methods=['POST'])
@token_required
def promote_user(current_user):
    if not current_user['isAdmin']:
        return jsonify({'message' : 'Cannot perform that function!'}),403

    query_parameters = request.args

    id = query_parameters.get('id')
   
    if not id:
        return page_not_found(404)

    try:
        id = int(id)
    except ValueError:
        return jsonify({'message':"'id' must be an integer"}),400
    
    user_data = {}
    user_data['isAdmin'] = True

    db.update_user(id,user_data)
    
    return jsonify({'message':"User {} is now Admin".format(id)}),201



# ------------- Measurement related paths -------------------------------------

@app.route('/api/v1/resources/measures/all', methods=['GET'])
@token_required
def api_all(current_user):
    return jsonify(db.get_all_measures(int(current_user['UserID']))),200

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message' : 'The resource could not be found'}),404

@app.route('/api/v1/resources/measures', methods=['GET', 'POST', 'DELETE'])
@token_required
def api_filter(current_user):

    if request.method == 'POST':
        required_fields = ("date","timeSlot")
        if not request.json or not all (f in request.json for f in required_fields):
            return jsonify({'message' : "Must provide json including 'date', and 'timeSlot' </p>"}),400
        
        dateArg = request.json['date']

        formato = '%Y-%m-%d %H:%M'
        try:
            date = dt.datetime.strptime(dateArg,formato)
        except ValueError:
            return jsonify({'message' : "Must use YYYY-MM-DD HH:MM as Date format"}),400

        timeSlot = string.lower(request.json['timeSlot'])
        if invalidTimeSlot(timeSlot):
            return jsonify({'message' : "Must use a valid Time Slot: <antes del desayuno> <antes del almuerzo> <antes de la merienda> <antes de la cena> <despues del desayuno> ..."}),400

        if "id" in request.json:
            new_measure = {}
            new_measure["id"] = request.json["id"]
            new_measure['value'] = request.json['value']
            new_measure['timeSlot'] = timeSlot
            new_measure['date'] = date
            return modify_measurent(new_measure)

        db.insert_measure(int(current_user['UserID']),timeSlot,date,request.json['value'])
        return jsonify({'message' : "The resource was succesfully added"}),201

    #For GET or DELETE a measurement Id is needed
    query_parameters = request.args

    id = query_parameters.get('id')
   
    if not id:
        return page_not_found(404)

    try:
        id = int(id)
    except ValueError:
        return jsonify({'message' : "'id' must be an integer"}),400


    #The user must have the correct credentials
    requestedMeasurement = db.get_measurement_with_id(id)
    if not (current_user['isAdmin'] or (requestedMeasurement['user_id'] == current_user['UserID'])):
            return jsonify({'message':'Unauthorized access'}),401
    
    if not requestedMeasurement:
        return jsonify({'message':'Measurement not found'}),404    
    
    #Send the results
    if request.method == 'GET':
        return jsonify(requestedMeasurement),200

    if request.method == 'DELETE':
        db.delete_measurement(id)
        return jsonify({'message':"Measurement with id={} deleted".format(id)}), 200
  



@app.route('/api/v1/resources/measures/between', methods=['GET'])
@token_required
def api_interval(current_user):
    query_parameters = request.args

    start = query_parameters.get('start')
    end = query_parameters.get('end')

    #Check if the input had parameters to run a query
    if not (start and end):
        return page_not_found(404)

    #Check if parameters are correctly formatted
    formato = '%Y-%m-%d'
    try:
    	startDate = dt.datetime.strptime(start,formato)
    	endDate = dt.datetime.strptime(end,formato) + dt.timedelta(days=1)
    except ValueError:
    	return jsonify({'message':"Must use YYYY-MM-DD as Date format."}), 400

    results = db.get_measurements(int(current_user['UserID']),startDate,endDate)
    return jsonify(results),200

@app.route('/api/v1/resources/print', methods=['GET'])
@token_required
def print_measures(current_user):

    #Generating Document
    back_to_months = 1

    query_parameters = request.args

    months_param = query_parameters.get('months')
    if months_param:
        back_to_months = int(months_param)
    
    pdf_file_name = "measurement_table.pdf"

    starting_date = dt.datetime.today() - relativedelta(months=back_to_months)
    end_date = dt.datetime.now()
    
    measurements = db.get_measurements(int(current_user['UserID']),starting_date,end_date,True)
    
    table_generator = Measurement_table(starting_date,end_date,measurements)

    #Begin Transfer
    response = send_file(pdf_file_name, as_attachment=True, attachment_filename=pdf_file_name,cache_timeout=0)
    response.headers["x-filename"] = pdf_file_name
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'

    return response
    

#Temp / test
@app.route('/api/v1/resources/download', methods=['GET'])
@token_required
def download(current_user):
    if not current_user['isAdmin']:
        return jsonify({'message' : 'Cannot perform that function!'}),403    

    query_parameters = request.args

    filename = query_parameters.get('file')

    #Check if the input had parameters to run a query and file exist
    if not filename:
        return jsonify({'message':"Must include filename <file> as argument"}),404

    if (not isfile(filename)):
        return jsonify({'message':"File '{}' not found".format(filename)}),404

    return send_file(filename, as_attachment=True, attachment_filename=filename)


if __name__== '__main__':
    #app.run(debug=True)
    app.run(host='192.168.0.108',port=5000,debug=True)


# To do - Inverstigar:
# Generar certificado y correr API en https: https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
