// Imports the Google Cloud client library
import {PubSub} from '@google-cloud/pubsub';
import { PublishedMessage } from '../schemas/pub-sub';

const topicName = 'movie-events';

// Creates a client; cache this for further use
const pubSubClient = new PubSub({
    projectId: "pcd-project-2"
});

export async function publishMessage(data: PublishedMessage) {
  // Publishes the message as a string, e.g. "Hello, world!" or JSON.stringify(someObject)
  
  const dataBuffer = Buffer.from(JSON.stringify(data));

  // Cache topic objects (publishers) and reuse them.
  const topic = pubSubClient.topic(topicName);

  try {
    const messageId = await topic.publishMessage({data: dataBuffer});
    console.log(`Message ${messageId} published.`);
    return messageId;
  } catch (error) {
    console.error(
      `Received error while publishing: ${(error as Error).message}`,
    );
    return 1;
  }
}

