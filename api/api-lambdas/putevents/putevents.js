const AWS = require('aws-sdk')
const { createMetricsLogger, Unit } = require("aws-embedded-metrics");
//var moment = require('moment-timezone');

var personalizeevents = new AWS.PersonalizeEvents();
//var dynamoClient = new AWS.DynamoDB.DocumentClient();

console.log('Loading function');

function getTimeZoneOffset(date, timeZone) {

  // Abuse the Intl API to get a local ISO 8601 string for a given time zone.
  let iso = date.toLocaleString('en-CA', { timeZone, hour12: false }).replace(', ', 'T');

  // Include the milliseconds from the original timestamp
  iso += '.' + date.getMilliseconds().toString().padStart(3, '0');

  // Lie to the Date object constructor that it's a UTC time.
  const lie = new Date(iso + 'Z');

  // Return the difference in timestamps, as minutes
  // Positive values are West of GMT, opposite of ISO 8601
  // this matches the output of `Date.getTimeZoneOffset`
  return -(lie - date) / 60 / 1000;
}

exports.handler = (event, context, callback) => {
    console.log(JSON.stringify(event, null, 2));
    
    event.Records.forEach(function(record) {
        // Kinesis data is base64 encoded so decode here
        const metrics = createMetricsLogger();
        metrics.putDimensions({ Type: "PutEvents" });

        var payload = Buffer.from(record.kinesis.data, 'base64').toString('ascii');
        //console.debug('Decoded payload:', payload);
        payload = JSON.parse(payload);

        if (payload.sp_event_id != undefined){
            metrics.setProperty("EventID", payload.sp_event_id);
        }

        if (payload.sp_derived_tstamp === undefined || payload.sp_derived_tstamp.trim().length === 0){
            console.debug("Skipping event: not valid sp_derived_tstamp")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }
        
        var eventDate = new Date(payload.sp_derived_tstamp);

        if (payload.sp_app_id === undefined || payload.sp_app_id != process.env.FilterAppId){
            console.debug("Skipping event: not valid sp_app_id")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }

        if (payload.content_contentId === undefined || payload.content_contentId.trim().length === 0){
            console.debug("Skipping event: not valid content_contentId")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }
        
        if (payload.page_type === undefined || payload.page_type != "article"){
            console.debug("Skipping event: not valid page_type")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }
        
        if (payload.sp_event_name === undefined || payload.sp_event_name != "page_view"){
            console.debug("Skipping event: not valid sp_event_name")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }

        if (payload.sp_domain_sessionid === undefined){
            console.debug("Skipping event: missing sp_domain_sessionid")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }

        if ((payload.sp_user_id === undefined || payload.sp_user_id.trim().length === 0) && (payload.sp_domain_userid === undefined || payload.sp_domain_userid.trim().length === 0)){
            console.debug("Skipping event: missing sp_user_id and sp_domain_userid")
            metrics.putMetric("EventStatus", 0);
            metrics.flush();
            return context.successful;
        }
        
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
        
        if (payload.page_rid != undefined){
            putEventsParams.eventList[0].recommendationId = payload.page_rid
        }
      
        console.log("THIS IS THE OBJECT = " + JSON.stringify(putEventsParams,null,3))
        console.log("THIS IS THE SOURCE OBJECT = " + JSON.stringify(payload,null,3))

        personalizeevents.putEvents(putEventsParams, function (err, data) {
          if (err) {
                console.log(err, err.stack); // an error occurred
                metrics.putMetric("EventStatus", -1);
          }
          else{ 
                metrics.putMetric("EventStatus", 1);
                metrics.flush();
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
