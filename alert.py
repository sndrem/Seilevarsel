#!/usr/bin/env python
# encoding=utf8 

# api.openweathermap.org/data/2.5/forecast?id=<citycode>&appid=<apikey>

import sys
import os
import json
from pprint import pprint
import requests
from datetime import datetime, date
from twilio.rest import Client

# Fetch environment-variables
try:
	account_sid = os.environ["TWILIO_ACCOUNT_SID"]
	auth_token = os.environ["TWILIO_AUTH_TOKEN"]
except:
	print("Could not fetch environment-variables for twili accout sid and twilio auth token")
	sys.exit(1)

client = Client(account_sid, auth_token)

LOG_FILE_NAME = "log.txt"
DAYS_UNTIL_NEXT_NOTIFICATION = 5



# Reads the preference file
def readPreferences(filename):
	with open(filename, "r") as preferences:
		return json.load(preferences)

# Method for downloading the weather
def downloadWeather(url, pref):
	print("Fetching weather data from url: " + url)
	response = requests.get(url)
	print("Response status: " + str(response.status_code))
	print("Headers: " + response.headers["content-type"])
	print("Encoding: " + response.encoding)
	print("")
	return response.json()
	

# Method for checking if the weather is good based on our preferences from preferences.json
# If the weather is good, we check the log and potenially sends an sms, if the weather is bad we send a text to notify the user
def checkWeather(data, pref):
	city = data['city']['name']
	country = data['city']['country']
	lastForecast = data['list'][-1] # Gets the last element in the list

	windPrefMin = pref['windPrefMin']
	windPrefMax = pref['windPrefMax']
	tempPrefMin = pref['tempPrefMin']
	tempPrefMax = pref['tempPrefMax']

	actualWindForecast = lastForecast['wind']['speed']
	actualTempForecast = lastForecast['main']['temp']

	windOkay = (actualWindForecast >= windPrefMin and actualWindForecast <= windPrefMax)
	tempOkay = (actualTempForecast >= tempPrefMin and actualTempForecast <= tempPrefMax)

	shouldSendMessage = checkLog(lastForecast, pref)
	if(windOkay and tempOkay):
		# Check log if we should send message
			# If log says go, send message and mail
		# if log is no go, don't do anything
		print("Lets go sailing, the wind is " + str(actualWindForecast) + " m/s and the temperature is " + str(actualTempForecast))		
		if shouldSendMessage:
			text = formatText(lastForecast, pref)
			sendMessage(text, pref)
			resetLog()

	else:
		print("Lets not go sailing. The weather is too bad")
		text = "Vaeret er for daarlig for seiling. Det er meldt %s m/s vind og %s grader den %s\nNy varsel kommer om %d dager" % (actualWindForecast, actualTempForecast, lastForecast['dt_txt'], DAYS_UNTIL_NEXT_NOTIFICATION)
		if shouldSendMessage:
			sendMessage(text, pref)
			resetLog()


# Checks the log to see if we should send a message or not. 
# A message is being sent if either messageSent = false, or if it is a week or more since we last sent a message
def checkLog(forecast, pref):
	with open(LOG_FILE_NAME, "r") as logFile:
		row = logFile.readlines()[0].split(",") # Read line, get the first line and split on comma
		dateUpdated = row[0]
		messageSent = row[1]
		dateSent = row[2]

		# If message has not been sent
		if(messageSent == 'false'):
			return True
		elif(messageSent == 'true'):
			# Check dateSent vs todays Date
			numberOfDays = compareDates(dateSent, dateUpdated)
			if(numberOfDays >= DAYS_UNTIL_NEXT_NOTIFICATION):
				print("Fem dager har gått, send ny melding")
				return True
			else:
				print("Det har enda ikke gått en uke. Ta det med ro...")
				return False

# Returns formatted text for sms-sending
def formatText(forecast, pref):
	windspeed = str(forecast['wind']['speed']) + " m/s"
	temperature = str(forecast['main']['temp']) + " grader"
	forecastDate = str(forecast['dt_txt'])
	text = "Hei %s\nDet er meldt bra seilevaer om fem dager.\nDet er meldt %s og %s den %s\nHer er lenke til seileplan: http://bsiseiling.no/en/seilplan/\nHer er lenke til skippere: http://bsiseiling.no/en/skippers/\nNy varsel kommer om %d dager" % (pref['name'], windspeed, temperature, forecastDate, DAYS_UNTIL_NEXT_NOTIFICATION)
	return text;

# Resets the log after a message has been sent
def resetLog():
	now = str(date.today())
	try:
		with open(LOG_FILE_NAME, "r+") as logFile:
			logFile.seek(0) # Set cursor at start of file
			logFile.truncate() # Delete the file content
			logFile.write("%s,%s,%s" % (now, "true", now)) # Rewrite file
	except IOError as e:
		with open(LOG_FILE_NAME, "w") as logFile:
			logFile.write("%s,%s,%s" % (now, "false", -1))

# sends a message to a predefined phone number stored in an environment variable
def sendMessage(body, pref):
	phoneNumber = os.environ['PHONE_NUMBER']
	print("Sending message %s to %s" % (body, phoneNumber))
	try:
		client.messages.create(
			to=phoneNumber,
			from_=os.environ['TWILIO_PHONE'],
			body=body
		)
		sys.exit()
	except:
		sys.exit(1)


# Returns how many day since last date
def compareDates(dateSent, now):
	dateFormat = "%Y-%m-%d"
	a = datetime.strptime(dateSent, dateFormat)
	b = datetime.strptime(now, dateFormat)
	delta = b - a
	return delta.days

# Updates the log with todays date and restores the previous fields for if a message has been sent and if so, when that message has been sent.
# The method checks if a log file exists, if no, then it just populates the log file with standard data as if no message has ever been sent
def updateLog(date):
	today = date.today()
	try:
		with open(LOG_FILE_NAME, "r+") as logFile:
			rows = logFile.readlines()[0].split(",")
			date = rows[0]
			messageSent = rows[1]
			dateSent = rows[2]

			logFile.seek(0) # Set cursor at start of file
			logFile.truncate() # Delete the file content
			logFile.write("%s,%s,%s" % (today, messageSent, dateSent)) # Rewrite file
	except IOError as e:
		with open(LOG_FILE_NAME, "w") as logFile:
			logFile.write("%s,%s,%s" % (today, "false", -1))

	

def main():
	updateLog(date)
	preferences = readPreferences("preferences.json")
	url = "http://api.openweathermap.org/data/2.5/forecast?id=" + preferences['bergenCityCode'] + "&appid=" + preferences['openWeatherApiKey'] + "&units=metric";
	weatherData = downloadWeather(url, preferences)
	checkWeather(weatherData, preferences)


if __name__ == '__main__':
		main()	