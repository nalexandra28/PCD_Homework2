const { PubSub } = require('@google-cloud/pubsub');

const topicName = 'event-notifications';

const pubSubClient = new PubSub({
    projectId: "pcd-project-2"
});

async function publishMessage(data) {
  
  const dataBuffer = Buffer.from(JSON.stringify(data));

  const topic = pubSubClient.topic(topicName);

  try {
    const messageId = await topic.publishMessage({data: dataBuffer});
    console.log(`Message ${messageId} published.`);
    return messageId;
  } catch (error) {
    console.error(
      `Received error while publishing: ${error.message}`,
    );
    throw error;
  }

}

module.exports = { publishMessage };

