const AWS = require('aws-sdk');
AWS.config.apiVersions = {
   dynamodb: '2012-08-10'
};
AWS.config.update(
    {   region: "us-east-2" ,
        endpoint: "http://dynamodb.us-east-2.amazonaws.com"    
    });
const docClient = new AWS.DynamoDB.DocumentClient({region : "us-east-2"});


exports.handler = (event, context, callback) => {
   console.log('event' + event);
   
   //Tämä skannaa koko tietokannan, pullonkaula & ei ole tehokasta
   
   let scanningParameters = {
       TableName: "measurements"
       
   };
   
   docClient.scan(scanningParameters, function(err, data){
       if(err){
           callback(err, null);
       }else{
           callback(null, data);
       }
           
   });
   
   
};