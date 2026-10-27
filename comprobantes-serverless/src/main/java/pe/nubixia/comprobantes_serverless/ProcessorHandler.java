package pe.nubixia.comprobantes_serverless;
import com.amazonaws.services.lambda.runtime.*;
import com.amazonaws.services.lambda.runtime.events.*;
import java.util.*;
public class ProcessorHandler implements RequestHandler<SQSEvent,SQSBatchResponse> {
 private final InvoiceService service=new InvoiceService(new AwsStore());
 public SQSBatchResponse handleRequest(SQSEvent event,Context context) {
  var failures=new ArrayList<SQSBatchResponse.BatchItemFailure>();
  for(var record:event.getRecords()) {
   try { service.process(record.getBody()); }
   catch(Exception e) {
    context.getLogger().log("documentId="+record.getBody()+" event=RETRY error="+e+"\n");
    failures.add(new SQSBatchResponse.BatchItemFailure(record.getMessageId()));
   }
  }
  return new SQSBatchResponse(failures);
 }
}