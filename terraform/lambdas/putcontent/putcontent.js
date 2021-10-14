const AWS = require('aws-sdk')
const { createMetricsLogger, Unit } = require("aws-embedded-metrics");

var personalizeevents = new AWS.PersonalizeEvents();
//var dynamoClient = new AWS.DynamoDB.DocumentClient();

console.log('Loading function');

exports.handler = (event, context, callback) => {
    console.log(JSON.stringify(event, null, 2));
    
    event.Records.forEach(function(record) {
        // Kinesis data is base64 encoded so decode here
        const metrics = createMetricsLogger();
        metrics.putDimensions({ Type: "PutContent" });

        var payload = Buffer.from(record.kinesis.data, 'base64').toString('ascii');
        console.debug('Decoded payload:', payload);
        payload = JSON.parse(payload);
        
        if (!payload.Published){
            console.debug('Skipping not published content', payload);
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }
/**
        if ((payload.sp_user_id === undefined || payload.sp_user_id.trim().length === 0) && (payload.sp_domain_userid === undefined || payload.sp_domain_userid.trim().length === 0)){
            console.debug("Skipping event: missing sp_user_id and sp_domain_userid")
            return context.successful;
        }
    **/
        var eventDate = new Date(payload.PublishedDate);
        var currentDate = new Date();
                
        var delay_ms = currentDate.getTime() - eventDate.getTime();
        metrics.putMetric("DeliveryLatencyMS", delay_ms, Unit.Milliseconds);

        var putItemsParams= {
            'datasetArn': process.env.CONTENT_DATASET_ARN,
            'items': [
                {
                  'itemId': payload.ContentId,
                  'properties': {
                      'ContentText': payload.ContentText,
                      'Category': payload.Category,
                      'WordCount': payload.WordCount,
                      'Published': payload.Published,
                      'ContentType': payload.ContentType,
                      'CREATION_TIMESTAMP': eventDate.getTime(),
                  }
                },
            ]
        }

        console.log("THIS IS THE OBJECT = " + JSON.stringify(putItemsParams,null,3))
        console.log("THIS IS THE SOURCE OBJECT = " + JSON.stringify(payload,null,3))

        personalizeevents.putItems(putItemsParams, function (err, data) {
          if (err) {
            metrics.putMetric("EventStatus", -1);
            metrics.flush();
            console.log(err, err.stack); // an error occurred
          }
          else{ 
                metrics.putMetric("EventStatus", 1);
                metrics.flush();
                console.log("Success: " + JSON.stringify(data, null, 2)) 
                //console.log(data);           // successful response
               // putItemsParams['items'][0]['CREATION_TIMESTAMP']=putItemsParams['items'][0]['CREATION_TIMESTAMP'].getTime();
                const putEventsErrResponse = {
                    statusCode: 500,
                    body: JSON.stringify(err),
                };
                callback(null, putEventsErrResponse);
                const response = {
                    statusCode: 200,
                    body: JSON.stringify(putItemsParams),
                };
                callback(null, response);
          }
        });
    
    });
};