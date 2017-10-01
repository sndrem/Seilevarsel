# Wind-alert

Script for notifying a phone number with wind forecast for Bergen, Norway a little week into the future. 

## Prerequisities
* Your phone number, set to environment variable = PHONE_NUMBER
* A twilio account_sid, set to environment variable = TWILIO_ACCOUNT_SID
* A twilio auth_token, set to environment variable = TWILIO_AUTH_TOKEN
* A twilio phone number that can send sms, set to environment variable = TWILIO_PHONE
* A open weather api key stored in preferences.json - A key can be obtained from [openweathermap.org/api](https://openweathermap.org/api)
* Your preferred city code found at open weather api - [Download city.list.json.gz](http://bulk.openweathermap.org/sample/) to find your id

