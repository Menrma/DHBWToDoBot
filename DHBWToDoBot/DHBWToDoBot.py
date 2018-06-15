import os
import json

from flask import Flask
from flask import request

from DatabaseHelper import DatabaseHelper

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "Database\TodoDB.db")

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def dialogflowWebhook():

	print("Incomming request on /webhook")	

	req = request.get_json(silent=True, force=True)

	print("Request:" )
	print(json.dumps(req, indent=4))

	processRequest(req)



#Method for processing the Request
def processRequest(req):
	# Get name of current intent
	intentName = req.get("queryResult").get("intent").get("displayName")

	#if intentName == "Begruessung Intent":



# Entry point of the application
if __name__ == "__main__":
	print("Starting Application...")
	app.run()
	#dbHelper = DatabaseHelper(DATABASE_PATH)
	##dbHelper.insertUser("Leyla", "123456789")

	#telegramID = "123456789"

	#res = dbHelper.checkUser(telegramID)
	#if(res):
	#	print("### TODAY ###")
	#	todayTodos = dbHelper.selectDayTodo(telegramID)
	#	print(todayTodos)
	#	print("### WEEK ###")
	#	weekTodos = dbHelper.selectWeekTodo(telegramID)
	#	print(weekTodos)
	#	print("### SPECIFIC DATE ###")
	#	dayTodos = dbHelper.selectDayTodo(telegramID, '2015-05-31')
	#	print(dayTodos)

	#	dbHelper.closeConnection()