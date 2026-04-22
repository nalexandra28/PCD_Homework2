const functions = require('@google-cloud/functions-framework');

functions.cloudEvent('processEvent', cloudEvent => {
 
  try {

    console.log('Function triggered');

    const message = cloudEvent.data?.message;

    if (!message || !message.data) {
      console.log('No message payload');
      return;
    }

    const messageId = cloudEvent.messageId;

    const decodedData = JSON.parse(
      Buffer.from(message.data, 'base64').toString()
    );

    console.log('Received event:', decodedData);

  } catch (error) {
    console.error('Error processing event:', error);
    throw error;
  }
});
