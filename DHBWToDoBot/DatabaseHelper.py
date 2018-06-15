import sys
import sqlite3
from sqlite3 import Error
import datetime

DATE_FORMAT = "%Y-%m-%d"

class DatabaseHelper(object):

	def __init__(self, path):
		""" Inits the class and opens the connection to the database"""
		try:
			dbConnection = sqlite3.connect(path)
			self.__dbCursor = dbConnection.cursor()
		except Error as e:
			print(e)

	def closeConnection(self):
		""" Closes the connection to the database """
		self.__dbCursor.close()

	def checkUser(self, telegramID):
		""" Method for checking if the user already exists and return """
		try:
			sql_command = 'SELECT * FROM User WHERE TelegramID=?'
			self.__dbCursor.execute(sql_command, (telegramID,))
			result = self.__dbCursor.fetchall()
			return result
		except:
			print("Unexpected error:", sys.exc_info()[0])

	def insertUser(self, username, telegramID):
		""" Method for inserting a new user to the database """
		try:
			sql_command = 'INSERT INTO User (Username, TelegramID) VALUES(?,?)'
			self.__dbCursor.execute(sql_command, (username, telegramID))
			#self.__dbCursor.commit()
			return True
		except:
			print("Unexpected error:", sys.exc_info()[0])
			return False

	def __getUserIdByTelegramID(self, telegramID):
		""" Private method for selecting the user_id given the telegram id """
		try:
			sql_command = 'SELECT DISTINCT ID FROM User WHERE TelegramID=?'
			self.__dbCursor.execute(sql_command, (telegramID,))
			result = self.__dbCursor.fetchone()
			return result[0]
		except:
			print("Unexpected error:", sys.exc_info()[0])

	def selectWeekTodo(self, telegramID):
		""" Method for selecting users ToDos for today + 7 days """
		user_id = self.__getUserIdByTelegramID(telegramID)
		if user_id:
			try:
				currentDate = self.__getCurrentDate()
				end_date = self.__calculateEndDate(currentDate, 7)
				sql_command = 'SELECT * FROM ToDos WHERE User_ID=? AND Datum BETWEEN date(?) AND date(?)'
				self.__dbCursor.execute(sql_command, (user_id, currentDate, end_date))
				result = self.__dbCursor.fetchall()
				return result
			except:
				print("Unexpected error:", sys.exc_info()[0])
				return None
		else:
			return None

	def selectDayTodo(self, telegramID, date=None):
		""" Method for selecting users ToDos on a specific date 
			if Date parameter is empty, date will be todays date """
		user_id = self.__getUserIdByTelegramID(telegramID)
		if not date:
			date = self.__getCurrentDate()

		if user_id:
			try:
				date_formatted = self.__formatStringToDate(date)
				result = self.__selectToDoByDay(user_id, date_formatted)
				return result
			except:				
				print("Unexpected error:", sys.exc_info()[0])
				return None
		else:
			return None

	def __selectToDoByDay(self, user_id, date):
		""" Private method for selecting users today by given user id
			and a specific date """
		try:
			sql_command = 'SELECT * FROM ToDos WHERE User_ID=? AND Datum=date(?)'
			self.__dbCursor.execute(sql_command, (user_id, date))
			result = self.__dbCursor.fetchall()
			return result
		except:
			print("Unexpected error:", sys.exc_info()[0])
			return None

	def __getCurrentDate(self):
		""" Private method retunrs the current date """
		return datetime.datetime.now().strftime(DATE_FORMAT)

	def __calculateEndDate(self, startDate, days):
		""" Private method for adding a number of days to the given date """
		begin_date = datetime.datetime.strptime(startDate, DATE_FORMAT)
		end_date = begin_date + datetime.timedelta(days=days)
		return self.__formatDate(end_date)

	def __formatDate(self, dateToFormat):
		""" Private method to format the date of a date object"""
		return dateToFormat.strftime(DATE_FORMAT)

	def __formatStringToDate(self, stringDateToFormat):
		""" Private method to format the date of a string object with a date in it"""
		dat = datetime.datetime.strptime(stringDateToFormat, DATE_FORMAT)
		return self.__formatDate(dat)