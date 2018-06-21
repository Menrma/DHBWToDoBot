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
		elif intentName == "Termin abfragen Datum":
			# Get date from request
			date = req.get("queryResult").get("parameters").get("Datum")
			if date:
				response = __processTerminAbfragenIntent(dbHelper, date)
			else:
				response = __proccessTerminHeuteIntent(dbHelper)
		elif intentName == "Termin abfragen Heute":
			response = __proccessTerminHeuteIntent(dbHelper)
		elif intentName == "Termin abfragen Woche":
			response = __proccessTerminWocheIntent(dbHelper)
		elif intentName == "Termin erstellen 2":
			#Get parameters from request
			datum = req.get("queryResult").get("parameters").get("Datum")
			uhrzeit = req.get("queryResult").get("parameters").get("Uhrzeit")
			dauer = req.get("queryResult").get("parameters").get("Dauer")
			ort = req.get("queryResult").get("parameters").get("Ort")
			titel = req.get("queryResult").get("parameters").get("Titel")
			repsonse = __processTerminErstellenIntent(dbHelper, datum, uhrzeit, dauer, ort, titel)
		elif intentName == "Termin löschen 2":
			datum = req.get("queryResult").get("parameters").get("Datum")
			uhrzeit = req.get("queryResult").get("parameters").get("Uhrzeit")
			titel = req.get("queryResult").get("parameters").get("any")
			response = __processTerminLoeschennIntent(dbHelper, datum, uhrzeit, titel)
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
		date = date[:10]
		dateOutput = __convertDateForOutput(date)
		dbResult = dbHelper.selectDayTodo(TEST_TELEGRAM_ID, date)
		if(dbResult):
			response = "Termine am {0}:\n".format(dateOutput)
			response += __generateResponseFromDBResult(dbResult)
			return response
		else:
			return "Für den {0} sind keine Aufgaben vorhanden".format(dateOutput)

def __proccessTerminHeuteIntent(dbhelper):
		todoToday = dbhelper.selectDayTodo(TEST_TELEGRAM_ID)
		if todoToday:
			response = "Aufgaben heute:\n"
			response += __generateResponseFromDBResult(todoToday)
			return response
		else:
			return "Heute sind keine Aufgaben vorhanden."

def __proccessTerminWocheIntent(dbhelper):
		weekResponse = dbhelper.selectWeekTodo(TEST_TELEGRAM_ID)
		if weekResponse:
			response = "Aufgaben kommende Woche:\n"
			response += __generateResponseFromDBResult(weekResponse)
			return response
		else:
			return "Für die kommende Woche sind keine Aufgaben vorhanden."

def __processTerminErstellenIntent(dbhelper, datum, uhrzeit, dauer, ort, titel):
	dt = datum[:10]
	uz = uhrzeit[11:-6]
	dateOutput = __convertDateForOutput(dt)
	insertResponse, res = dbhelper.insertToDo(TEST_TELEGRAM_ID, dt, uz, ort, dauer, titel)
	if insertResponse == 0:
		# zu diesem Zeitpunkt gibt es bereit einen Termin
		return ""
	elif insertResponse == 1:
		# Fehler
		return ""
	elif insertResponse == 2:
		# Hat funktioniert
		return "Termin {0} am {1} um {2} wurde erfolgreich angelegt.".format(titel, dateOutput, uz)

def __processTerminLoeschennIntent(dbhelper, datum, uhrzeit, titel):
	dt = datum[:10]
	uz = uhrzeit[11:-6]
	dateOutput = __convertDateForOutput(dt)
	deleteResponse = dbhelper.deleteToDo(TEST_TELEGRAM_ID, dt, uz, titel)
	if deleteResponse == 0:
		return "Am {0} um {1} ist keine Aufgabe vorhanden.".format(dt, uz)
	elif deleteResponse == 1:
		return "Es ist ein Fehler beim Löschen der Aufgabe am {0} um {1} Uhr aufgetreten".format(dateOutput, uz)
	elif deleteResponse == 2:
		if titel:
			return "Die Aufgabe mit dem Titel {0} am {1} um {2} wurde erfolgreich gelöscht.".format(titel, dateOutput, uz)
		else:
			return "Die Aufgabe am {0} um {1} wurde erfolgreich gelöscht.".format(dateOutput, uz)

def __generateResponseFromDBResult(dbResult):
	response = ""
	for entry in dbResult:
		if not entry[5] and not entry[6]:
			response += "Titel: {0}, Uhrzeit: {1}".format(entry[2], entry[3])
		elif not entry[5]:
			response += "Titel: {0}, Uhrzeit: {1}, Ort: {2}".format(entry[2], entry[3], entry[6])
		elif not entry[6]:
			response += "Titel: {0}, Uhrzeit: {1}, Dauer: {2}".format(entry[2], entry[3], entry[5])
		else:
			response += "Titel: {0}, Uhrzeit: {1}, Dauer: {2}, Ort: {3}".format(entry[2], entry[3], entry[5], entry[6])
	return response

# Entry point of the application
if __name__ == "__main__":
	print("Starting Application...")
	app.run()