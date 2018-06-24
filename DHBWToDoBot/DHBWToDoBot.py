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
	#ret = __createSimpleTextResponse(ret)
	ret = __createTelegramTextResponse(ret)
	r = make_response(jsonify(ret))
	return r

#Method for processing the Request
def processRequest(req):
	dbHelper = None
	sourceIsTelegram = False
	telegramId = ""
	try:
		dbHelper = DatabaseHelper(DATABASE_PATH)
		response = None
		# Get name of current intent
		intentName = req.get("queryResult").get("intent").get("displayName")

		if intentName != "Termin aendern 4":
			dbHelper.clearTodoChangeTable(TEST_TELEGRAM_ID)

		# check if source is telegram
		source = req.get("originalDetectIntentRequest").get("source")
		username = ""
		if source:
			if source == "telegram":
				sourceIsTelegram = True
				# Get Telegram Id
				telegramId = req.get("originalDetectIntentRequest").get("payload").get("data").get("message").get("chat").get("id")

		if intentName == "Begruessung Intent":
			#Get Username
			if sourceIsTelegram:
				username = req.get("originalDetectIntentRequest").get("payload").get("data").get("message").get("chat").get("first_name")
				response = __processBegruessungIntent(dbHelper, TEST_TELEGRAM_ID, username)
			else:
				response = __processBegruessungIntent(dbHelper, TEST_TELEGRAM_ID, username)
		elif intentName == "Termin abfragen Datum":
			# Get date from request
			date = req.get("queryResult").get("parameters").get("Datum")
			if date:
				response = __processTerminAbfragenIntent(dbHelper, TEST_TELEGRAM_ID, date)
			else:
				response = __proccessTerminHeuteIntent(dbHelper)
		elif intentName == "Termin abfragen Heute":
			response = __proccessTerminHeuteIntent(dbHelper, TEST_TELEGRAM_ID)
		elif intentName == "Termin abfragen Woche":
			response = __proccessTerminWocheIntent(dbHelper, TEST_TELEGRAM_ID)
		elif intentName == "Termin erstellen 2":
			#Get parameters from request
			datum = req.get("queryResult").get("parameters").get("Datum")
			uhrzeit = req.get("queryResult").get("parameters").get("Uhrzeit")
			dauer = req.get("queryResult").get("parameters").get("Dauer")
			ort = req.get("queryResult").get("parameters").get("Ort")
			titel = req.get("queryResult").get("parameters").get("Titel")
			response = __processTerminErstellenIntent(dbHelper, TEST_TELEGRAM_ID, datum, uhrzeit, dauer, ort, titel)
		elif intentName == "Termin löschen 2":
			datum = req.get("queryResult").get("parameters").get("Datum")
			uhrzeit = req.get("queryResult").get("parameters").get("Uhrzeit")
			titel = req.get("queryResult").get("parameters").get("Titel")
			response = __processTerminLoeschenIntent(dbHelper, TEST_TELEGRAM_ID, datum, uhrzeit, titel)
		elif intentName == "Termin aendern 2":
			datum = req.get("queryResult").get("parameters").get("Datum")
			uhrzeit = req.get("queryResult").get("parameters").get("Uhrzeit")
			response = __processTerminChangeIntent(dbHelper, TEST_TELEGRAM_ID, datum, uhrzeit)
		elif intentName == "Termin aendern 4":
			datum = req.get("queryResult").get("parameters").get("Datum")
			uhrzeit = req.get("queryResult").get("parameters").get("Uhrzeit")
			titel = req.get("queryResult").get("parameters").get("Titel")
			response = __processTermin4ChangeIntent(dbHelper, TEST_TELEGRAM_ID, datum, uhrzeit, titel)
	except:
		print("Unexpected error:", sys.exc_info()[0])
	finally:
		dbHelper.closeConnection()

	print ("Intent: {0} / Response: {1}".format(intentName, response))
	return response
	
def __createSimpleTextResponse(data):
	return {"fulfillmentText" : data};

def __createTelegramTextResponse(data):
	return {"payload" :	{ "telegram" : { "parse_mode" : "HTML", "text" : data}}}

def __convertDateForOutput(date):
	dateSplit = date.split('-')
	return "{0}.{1}.{2}".format(dateSplit[2], dateSplit[1], dateSplit[0])

def __processBegruessungIntent(dbHelper, telegramId, username):
	dbResult = dbHelper.checkUser(telegramId)
	if dbResult:
		username = dbResult[0][1]
		return "Hallo {0}, wie kann ich dir helfen?".format(username)
	else:
		# User is not known => Save
		insertResult = dbHelper.insertUser(username, telegramId)
		if insertResult:
			return "Hallo {0}, wie kann ich dir helfen?".format(username)
		else:
			return "Es tut mir Leid, der Benutzer {1} konnte nicht angelegt werden.".format(username)


def __processTerminAbfragenIntent(dbHelper, telegramId, date):
		date = date[:10]
		dateOutput = __convertDateForOutput(date)
		dbResult = dbHelper.selectDayTodo(telegramId, date)
		if(dbResult):
			response = "Termine am {0}:\n".format(dateOutput)
			response += __generateResponseFromDBResult(dbResult)
			return response
		else:
			return "Für den {0} sind keine Aufgaben vorhanden".format(dateOutput)

def __proccessTerminHeuteIntent(dbhelper, telegramId):
		todoToday = dbhelper.selectDayTodo(telegramId)
		if todoToday:
			response = "Aufgaben heute:\n"
			response += __generateResponseFromDBResult(todoToday)
			return response
		else:
			return "Heute sind keine Aufgaben vorhanden."

def __proccessTerminWocheIntent(dbhelper, telegramId):
		weekResponse = dbhelper.selectWeekTodo(telegramId)
		if weekResponse:
			response = "Aufgaben kommende Woche:\n"
			response += __generateResponseFromDBResult(weekResponse)
			return response
		else:
			return "Für die kommende Woche sind keine Aufgaben vorhanden."

def __processTerminErstellenIntent(dbhelper, telegramId, datum, uhrzeit, dauer, ort, titel):
	dt = datum[:10]
	uz = uhrzeit[11:-6]
	dateOutput = __convertDateForOutput(dt)
	insertResponse, res = dbhelper.insertToDo(telegramId, dt, uz, ort, dauer, titel)
	if insertResponse == 0:
		# zu diesem Zeitpunkt gibt es bereit einen Termin
		return "Am {0} um {1} gibt es bereits einen Termin mit dem Titel: {2}".format(dateOutput, uz, res[0][2])
	elif insertResponse == 1:
		# Fehler
		return "Es ist ein Fehler beim Anlegen der Aufgabe mit dem Titel {0} am {1} um {2} aufgetreten.".format(titel, dateOutput, uz)
	elif insertResponse == 2:
		# Hat funktioniert
		return "Termin {0} am {1} um {2} wurde erfolgreich angelegt.".format(titel, dateOutput, uz)

def __processTerminChangeIntent(dbhelper, telegramId, datum, uhrzeit):
	dt = datum[:10]
	uz = uhrzeit[11:-6]
	dateOutput = __convertDateForOutput(dt)
	insrtResp = dbhelper.insertToDoChange(telegramId, dt, uz)
	if insrtResp == 0:
		return "Es existiert kein Termin am {0} um {1} Uhr.".format(dateOutput, uz)
	elif insrtResp == 1:
		return "Es ist ein unerwarteter Fehler aufgetreten. Bitte erneut versuchen."
	elif insrtResp == 2:
		return "Welche Daten sollen geändert werden? Der Titel, das Datum oder die Uhrzeit?"

def __processTermin4ChangeIntent(dbhelper, telegramId, datum, uhrzeit, titel):
	dt = ""
	uz = ""
	ttl =  ""
	if datum:
		dt = datum[0]
		dt = dt[:10]
	if uhrzeit:
		uz = uhrzeit[0]
		uz = uz[11:-6]
	if dt:
		dateOutput = __convertDateForOutput(dt)
	if titel:
		ttl = titel[0]
	insertResponse = dbhelper.updateToDo(telegramId, dt, uz, ttl)
	if insertResponse == 0:
		return "Es existiert kein Termin zu diesem Zeitpunkt."
	elif insertResponse == 1:
		return "Es ist ein unerwarteter Fehler aufgetreten. Bitte erneut versuchen."
	elif insertResponse == 2:
		return "Termin wurde erfolgreich geändert."

def __processTerminLoeschenIntent(dbhelper, telegramId, datum, uhrzeit, titel):
	dt = datum[:10]
	uz = uhrzeit[11:-6]
	dateOutput = __convertDateForOutput(dt)
	deleteResponse = dbhelper.deleteToDo(telegramId, dt, uz, titel)
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
		dat = __convertDateForOutput(entry[3])
		if not entry[5] and not entry[6]:
			response += " - <b>Titel:</b> {0}, <b>Datum:</b> {1}, <b>Uhrzeit:</b> {2} Uhr\n".format(entry[2], dat, entry[4])
		elif not entry[5]:
			response += " - <b>Titel:</b> {0}, <b>Datum:</b> {1}, <b>Uhrzeit:</b> {2} Uhr, <b>Ort:</b> {3}\n".format(entry[2], dat, entry[4], entry[6])
		elif not entry[6]:
			response += " - <b>Titel:</b> {0}, <b>Datum:</b> {1}, <b>Uhrzeit:</b> {2} Uhr, <b>Dauer:</b> {3}\n".format(entry[2], dat, entry[4], entry[5])
		else:
			response += " - <b>Titel:</b> {0}, <b>Datum:</b> {1}, <b>Uhrzeit:</b> {2} Uhr, <b>Dauer:</b> {3}, <b>Ort:</b> {4}\n".format(entry[2], dat, entry[4], entry[5], entry[6])
	return response

#def __generateAdvancedResponseFromDBResult(dbResult):	
#	response = ""
#	for entry in dbResult:
#		dat = __convertDateForOutput(entry[3])
#		if not entry[5] and not entry[6]:
#			response += " - <b>Titel:</b> {0}\n<b>    - Datum:</b> {1}\n<b>    - Uhrzeit:</b> {2} Uhr\n".format(entry[2], dat, entry[4])
#		elif not entry[5]:
#			response += " - <b>Titel:</b> {0}\n<b>    - Datum:</b> {1}\n<b>    - Uhrzeit:</b> {2} Uhr\n<b>    - Ort:</b> {3}\n".format(entry[2], dat, entry[4], entry[6])
#		elif not entry[6]:
#			response += " - <b>Titel:</b> {0}\n<b>    - Datum:</b> {1}\n<b>    - Uhrzeit:</b> {2} Uhr\n<b>    - Dauer:</b> {3}\n".format(entry[2], dat, entry[4], entry[5])
#		else:
#			response += " - <b>Titel:</b> {0}\n<b>    - Datum:</b> {1}\n<b>    - Uhrzeit:</b> {2} Uhr\n<b>    - Dauer:</b> {3}\n<b>    - Ort:</b> {4}\n".format(entry[2], dat, entry[4], entry[5], entry[6])
#	return response

# Entry point of the application
if __name__ == "__main__":
	print("Starting Application...")
	app.run()
	#dbHelper = DatabaseHelper(DATABASE_PATH)

	#dbHelper.updateToDo(TEST_TELEGRAM_ID, '2018-06-20', '2018-06-25', None, None, None, None)
	#dbHelper.updateToDo(TEST_TELEGRAM_ID, '2018-06-20', '2018-06-25', None, None, None, None)