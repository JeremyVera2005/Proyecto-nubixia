package pe.nubixia.comprobantes_serverless;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;

class UserIsolationTest {
 @Test void claimsMustComeFromGatewayAuthorizer() {
  var event=new APIGatewayProxyRequestEvent().withHeaders(Map.of("sub","attacker","Authorization","made-up-token"));
  assertNull(ApiHandler.authenticatedUser(event));
  var context=new APIGatewayProxyRequestEvent.ProxyRequestContext();
  context.setAuthorizer(Map.of("claims",Map.of("sub","user-a")));event.setRequestContext(context);
  assertEquals("user-a",ApiHandler.authenticatedUser(event));
 }
 @Test void cannotReadAnotherUsersDocumentOrLegacySharedDocuments() {
  var db=mock(DynamoDbClient.class);
  var store=new AwsStore("user-a",db,null,null,"table","bucket");
  when(db.getItem(any(GetItemRequest.class))).thenReturn(GetItemResponse.builder().item(Map.of("owner",AttributeValue.fromS("user-b"),"payload",AttributeValue.fromS("invalid but never decoded"))).build());
  assertTrue(store.find("a".repeat(64)).isEmpty());
  when(db.getItem(any(GetItemRequest.class))).thenReturn(GetItemResponse.builder().item(Map.of("payload",AttributeValue.fromS("legacy"))).build());
  assertTrue(store.find("a".repeat(64)).isEmpty());
 }
 @Test void sameInvoiceBelongsToDistinctNamespaces() {
  var db=mock(DynamoDbClient.class);when(db.putItem(any(PutItemRequest.class))).thenReturn(PutItemResponse.builder().build());
  var a=new InvoiceService(new AwsStore("user-a",db,null,null,"table","bucket")).receive(InvoiceServiceTest.invoice("1"));
  var b=new InvoiceService(new AwsStore("user-b",db,null,null,"table","bucket")).receive(InvoiceServiceTest.invoice("1"));
  assertNotEquals(a.document().documentId(),b.document().documentId());
  var calls=ArgumentCaptor.forClass(PutItemRequest.class);verify(db,times(2)).putItem(calls.capture());
  assertEquals("user-a",calls.getAllValues().get(0).item().get("owner").s());
 }
 @Test void workerUpdatePreservesOwnerInsteadOfReplacingWholeItem() {
  var db=mock(DynamoDbClient.class);when(db.updateItem(any(UpdateItemRequest.class))).thenReturn(UpdateItemResponse.builder().build());
  var store=new AwsStore(null,db,null,null,"table","bucket");
  var d=new Document("a".repeat(64),"fingerprint",InvoiceServiceTest.invoice("1"),"RECIBIDO","date","date",List.of(),null,0);
  assertTrue(store.replace(d,d.transition("ACEPTADO","ready",0)));
  var request=ArgumentCaptor.forClass(UpdateItemRequest.class);verify(db).updateItem(request.capture());
  assertEquals("SET #p = :next",request.getValue().updateExpression());
  assertEquals("#p = :old",request.getValue().conditionExpression());
  verify(db,never()).putItem(any(PutItemRequest.class));
 }
}
