const AWS = require('aws-sdk')
var personalizeevents = new AWS.PersonalizeEvents();
//var dynamoClient = new AWS.DynamoDB.DocumentClient();

console.log('Loading function');

exports.handler = (event, context, callback) => {
    console.log(JSON.stringify(event, null, 2));
    
    event.Records.forEach(function(record) {
        // Kinesis data is base64 encoded so decode here
        var payload = Buffer.from(record.kinesis.data, 'base64').toString('ascii');
        console.debug('Decoded payload:', payload);
        payload = JSON.parse(payload);

        if (payload.sp_app_id == undefined || payload.sp_app_id != "theglobeandmail-website"){
            console.debug("Skipping event: not valid sp_app_id")
            return context.successful;

        }

        if (payload.content_contentId === undefined || payload.content_contentId.trim().length === 0){
            console.debug("Skipping event: not valid content_contentId")
            return context.successful;
        }
        
        if (payload.sp_derived_tstamp === undefined || payload.sp_derived_tstamp.trim().length === 0){
            console.debug("Skipping event: not valid sp_derived_tstamp")
            return context.successful;
        }
        
        if (payload.page_type == undefined || payload.page_type != "article"){
            console.debug("Skipping event: not valid page_type")
            return context.successful;
        }
        
        if (payload.sp_event_name == undefined || payload.sp_event_name != "page_view"){
            console.debug("Skipping event: not valid sp_event_name")
            return context.successful;
        }

        if (payload.sp_domain_sessionid == undefined){
            console.debug("Skipping event: missing sp_domain_sessionid")
            return context.successful;
        }
        
        if (payload.sp_derived_tstamp == undefined){
            console.debug("Skipping event: missing sp_derived_tstamp")
            return context.successful;
        }
        
        if ((payload.sp_user_id === undefined || payload.sp_user_id.trim().length === 0) && (payload.sp_domain_userid === undefined || payload.sp_domain_userid.trim().length === 0)){
            console.debug("Skipping event: missing sp_user_id and sp_domain_userid")
            return context.successful;
        }
        
        var eventDate = new Date(payload.sp_derived_tstamp);
        
        var putEventsParams= {
            'sessionId': payload.sp_domain_sessionid,
            'trackingId': process.env.TRACKING_ID,
            'userId': payload.sp_user_id ? payload.sp_user_id : payload.sp_domain_userid,
            eventList: [
                {
                  'eventId': payload.sp_evenet_id,
                  'eventType': payload.sp_event_name, 
                  'itemId': payload.content_contentId,
                  'sentAt': eventDate,
                 
                  'properties': {
                      'visitor_type': payload.visitor_type,
                      'visitor_countryCode': payload.visitor_countryCode,
                      'device_detector_visitorPlatform': payload.device_detector_visitorPlatform,
                      'device_detector_brandName': payload.device_detector_brandName,
                      'device_detector_browserFamily': payload.device_detector_browserFamily,
                      //'ContentText': null,
                      //'Category': null,
                      //'WordCount': null
                  }, 
                },
            ]
        }
        console.log("THIS IS THE OBJECT = " + JSON.stringify(putEventsParams,null,3))
        console.log("THIS IS THE SOURCE OBJECT = " + JSON.stringify(payload,null,3))

        personalizeevents.putEvents(putEventsParams, function (err, data) {
          if (err) {
                console.log(err, err.stack); // an error occurred
          }
          else{ 
                console.log("Success: " + JSON.stringify(data, null, 2)) 
                //console.log(data);           // successful response
                putEventsParams['eventList'][0]['sentAt']=putEventsParams['eventList'][0]['sentAt'].toTimeString();
                const putEventsErrResponse = {
                    statusCode: 500,
                    body: JSON.stringify(err),
                };
                callback(null, putEventsErrResponse);
                const response = {
                    statusCode: 200,
                    body: JSON.stringify(putEventsParams),
                };
                callback(null, response);
          }
        });
    
    });
};