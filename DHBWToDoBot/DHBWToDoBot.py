import os
import sys

from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify

from DatabaseHelper import DatabaseHelper

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "Database\TodoDB.db")

TEST_TELEGRAM_ID = "123456789"

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def dialogflowWebhook():

	print("Incomming request on /webhook")	

	req = request.get_json(silent=True, force=True)

	ret = processRequest(req)
	ret = __createSimpleTextResponse(ret)
	r = make_response(jsonify(ret))
	return r

#Method for processing the Request
def processRequest(req):
	dbHelper = None
	try:
		dbHelper = DatabaseHelper(DATABASE_PATH)
		response = None
		# Get name of current intent
		intentName = req.get("queryResult").get("intent").get("displayName")

		if intentName == "Begruessung Intent":
			response = __processBegruessungIntent(dbHelper)
		elif intentName == "Termin abfragen":
			# Get date from request
			date = req.get("queryResult").get("parameters").get("date")
			date = date[:10]
			response = __processTerminAbfragenIntent(dbHelper, date)
	except:
		print("Unexpected error:", sys.exc_info()[0])
	finally:
		dbHelper.closeConnection()

	return response
	
def __createSimpleTextResponse(data):
	return {"fulfillmentText" : data};

def __convertDateForOutput(date):
	dateSplit = date.split('-')
	return "{0}.{1}.{2}".format(dateSplit[2], dateSplit[1], dateSplit[0])

def __processBegruessungIntent(dbHelper):
	dbResult = dbHelper.checkUser(TEST_TELEGRAM_ID)
	if dbResult:
		username = dbResult[0][1]
		return "Hallo {0}, wie kann ich dir helfen?".format(username)
	else:
		return "Hallo, ich bin Dein persönlicher Assistent und werde Dich bei der Planung Deiner Termine unterstützen. Möchtest Du einen Termin erstellen?"

def __processTerminAbfragenIntent(dbHelper, date):
		dateOutput = __convertDateForOutput(date)
		dbResult = dbHelper.selectDayTodo(TEST_TELEGRAM_ID, date)
		if(dbResult):
			return None
		else:
			return "Für den {0} sind keine Aufgaben vorhanden".format(dateOutput)

# Entry point of the application
if __name__ == "__main__":
	print("Starting Application...")
	app.run()