package pe.nubixia.comprobantes_serverless;
import com.amazonaws.services.lambda.runtime.*;
import com.amazonaws.services.lambda.runtime.events.DynamodbEvent;
import software.amazon.awssdk.services.sqs.SqsClient;

/** Durable outbox: only INSERT records are published; status updates do not requeue. */
public class PublisherHandler implements RequestHandler<DynamodbEvent,Void> {
 private final SqsClient sqs=SqsClient.builder().httpClientBuilder(software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient.builder()).build();
 public Void handleRequest(DynamodbEvent event,Context context) {
  for(var record:event.getRecords()) {
   if(!"INSERT".equals(record.getEventName())) continue;
   String id=record.getDynamodb().getKeys().get("documentId").getS();
   sqs.sendMessage(r->r.queueUrl(System.getenv("QUEUE_URL")).messageBody(id));
   context.getLogger().log("documentId="+id+" event=ENCOLADO\n");
  }
  return null;
 }
}