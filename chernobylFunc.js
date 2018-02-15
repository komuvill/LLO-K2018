const AWS = require('aws-sdk')

AWS.config.apiVersions = {
   dynamodb: '2012-08-10'
}

AWS.config.update({ region: "us-east-2" })

const db = new AWS.DynamoDB({ endpoint: new AWS.Endpoint('http://dynamodb.us-east-2.amazonaws.com') })

exports.handler = (event, context, callback) => {
   console.log('event' + event)

   const weatherParameters = {
   "TableName": "measurements",
   "Item": {
   "id": { 'S': event.timestamp }, //päivämäärästä ja kellonajasta luotu uniikki primary key
   "temperature": { 'S': event.temperature }, // mitattu lämpötila
   "date" : {'S' : event.date }, // päivämäärä
   "time" : {'S' : event.time } // kellonaika
   }
}

db.putItem(weatherParameters, function (err, data) {
   if (err) {
      callback(null, "Jotain meni pieleen: " + err)
   } else {
      callback(null, "Havainnot tallennettiin tietokantaan")
      } 
   })
}