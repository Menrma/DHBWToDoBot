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
			self.__dbCon = dbConnection
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
			self.__dbCon.commit()
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
				sql_command = 'SELECT * FROM ToDos WHERE User_ID=? AND Datum BETWEEN date(?) AND date(?) ORDER BY Datum, Uhrzeit'
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

	def deleteToDo(self, telegramID, datum, uhrzeit, titel):
		user_id = self.__getUserIdByTelegramID(telegramID)
		if user_id:
			sql_command = "SELECT * FROM ToDos WHERE User_ID=? AND Datum=? AND Uhrzeit=?"
			try:
				self.__dbCursor.execute(sql_command, (user_id, datum, uhrzeit))
				result = self.__dbCursor.fetchall()
				if not result:
					return 0
				else:
					sql_command = 'DELETE FROM ToDos WHERE User_ID=? AND Datum=? AND Uhrzeit=?'
					if titel:
						sql_command += ' AND Titel=?'
						self.__dbCursor.execute(sql_command, (user_id, datum, uhrzeit, titel))
					else:
						self.__dbCursor.execute(sql_command, (user_id, datum, uhrzeit))

				self.__dbCon.commit()
				return 2
			except:				
				print("Unexpected error:", sys.exc_info()[0])
				return 1
		else:
			return 1

	def insertToDo(self, telegramID, datum, uhrzeit, ort, dauer, titel):
		user_id = self.__getUserIdByTelegramID(telegramID)
		if user_id:
			# check if there is a todo on this date at this time
			sql_command = "SELECT * FROM ToDos WHERE User_ID=? AND Datum=? AND Uhrzeit=?"
			try:
				self.__dbCursor.execute(sql_command, (user_id, datum, uhrzeit))
				result = self.__dbCursor.fetchall()
				if result:
					return (0, result)
				else:
					# there's no todo on this date at this time
					sql_command = "INSERT INTO ToDos (User_ID, Titel, Datum, Uhrzeit, Dauer, Ort) VALUES (?,?,?,?,?,?)"
					self.__dbCursor.execute(sql_command, (user_id, titel, datum, uhrzeit, dauer, ort))
					self.__dbCon.commit()
					return (2, None)
			except:				
				print("Unexpected error:", sys.exc_info()[0])
				return (1, None)
		else:
			return (1, None)

	def insertToDoChange(self, telegramID, datum, uhrzeit):
		user_id = self.__getUserIdByTelegramID(telegramID)
		if user_id:
			sql_command = "SELECT * FROM ToDos WHERE User_ID=? AND Datum=? AND Uhrzeit=?"
			try:
				self.__dbCursor.execute(sql_command, (user_id, datum, uhrzeit))
				result = self.__dbCursor.fetchall()
				if not result:
					return 0
				else:
					sql_command = "INSERT INTO TodoChange (User_ID, ToDo_ID) VALUES (?,?)"
					self.__dbCursor.execute(sql_command, (user_id, result[0][0]))
					self.__dbCon.commit()
					return 2
			except:				
				print("Unexpected error:", sys.exc_info()[0])
				return 1
		else:
			return 1

	def updateToDo(self, telegramID, datumNeu, uhrzeitNeu, titelNeu):
		user_id = self.__getUserIdByTelegramID(telegramID)
		if user_id:
			sql_commnd = "SELECT * FROM TodoChange WHERE User_ID=?"
			try:
				self.__dbCursor.execute(sql_commnd, (user_id,))
				result = self.__dbCursor.fetchall()
				if not result:
					return 0
				else:
					updated = False
					if datumNeu:
						sql_commnd = "UPDATE ToDos SET Datum=? WHERE ID=?"
						self.__dbCursor.execute(sql_commnd, (datumNeu, result[0][1]))
						self.__dbCon.commit()
						updated = True
					elif uhrzeitNeu:
						sql_commnd = "UPDATE ToDos SET Uhrzeit=? WHERE ID=?"
						self.__dbCursor.execute(sql_commnd, (uhrzeitNeu, result[0][1]))
						self.__dbCon.commit()
						updated = True
					elif titelNeu:
						sql_commnd = "UPDATE ToDos SET Titel=? WHERE ID=?"
						self.__dbCursor.execute(sql_commnd, (titelNeu, result[0][1]))
						self.__dbCon.commit()
						updated = True
						
					if updated:
						self.clearTodoChangeTable(telegramID)
						return 2
					else:
						return 1
			except:
				print("Unexpected error:", sys.exc_info()[0])
				return 1
		else:
			return 1

	def __selectToDoByDay(self, user_id, date):
		""" Private method for selecting users today by given user id
			and a specific date """
		try:
			sql_command = 'SELECT * FROM ToDos WHERE User_ID=? AND Datum=date(?) ORDER BY Datum, Uhrzeit'
			self.__dbCursor.execute(sql_command, (user_id, date))
			result = self.__dbCursor.fetchall()
			return result
		except:
			print("Unexpected error:", sys.exc_info()[0])
			return None

	def clearTodoChangeTable(self, telegramID):
		user_id = self.__getUserIdByTelegramID(telegramID)
		if user_id:
			try:
				sql_command = "DELETE FROM TodoChange WHERE User_ID=?"
				self.__dbCursor.execute(sql_command, (user_id,))
				self.__dbCon.commit()
				return True
			except:
				print("Unexpected error:", sys.exc_info()[0])
				return False
		else:
			return False

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