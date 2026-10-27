package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.util.*;
import java.time.Duration;
import software.amazon.awssdk.services.dynamodb.*;
import software.amazon.awssdk.services.dynamodb.model.*;
import software.amazon.awssdk.services.s3.*;
import software.amazon.awssdk.services.s3.model.*;
import software.amazon.awssdk.services.s3.presigner.*;
import software.amazon.awssdk.core.sync.RequestBody;

public final class AwsStore implements Store {
 private final String owner;
 public AwsStore() { this(null); }
 public AwsStore(String owner) { this(owner,Clients.DB,Clients.S3,Clients.SIGNER,System.getenv("TABLE_NAME"),System.getenv("BUCKET_NAME")); }
 AwsStore(String owner,DynamoDbClient db,S3Client s3,S3Presigner signer,String table,String bucket) {
  this.owner=owner;this.db=db;this.s3=s3;this.signer=signer;this.table=table;this.bucket=bucket;
 }
 @Override public String namespace() { return owner==null ? "" : owner+"|"; }
 private final DynamoDbClient db;
 private final S3Client s3;
 private final S3Presigner signer;
 private final String table,bucket;
 private static final class Clients {
  static final DynamoDbClient DB=DynamoDbClient.builder().httpClientBuilder(software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient.builder()).build();
  static final S3Client S3=S3Client.builder().httpClientBuilder(software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient.builder()).build();
  static final S3Presigner SIGNER=S3Presigner.create();
 }
 private Map<String,AttributeValue> key(String id) { LocalStore.checkId(id); return Map.of("documentId", AttributeValue.fromS(id)); }
 private Map<String,AttributeValue> item(Document d) {
  var result = new HashMap<>(Map.of("documentId", AttributeValue.fromS(d.documentId()), "payload", AttributeValue.fromS(encode(d))));
  if(owner!=null) result.put("owner",AttributeValue.fromS(owner));
  return result;
 }
 public boolean create(Document d) {
  try {
   db.putItem(PutItemRequest.builder().tableName(table).item(item(d)).conditionExpression("attribute_not_exists(documentId)").build()); return true;
  } catch (ConditionalCheckFailedException e) { return false; }
 }
 public Optional<Document> find(String id) {
  var item = db.getItem(GetItemRequest.builder().tableName(table).key(key(id)).consistentRead(true).build()).item();
  return item.isEmpty() || (owner!=null && !owner.equals(item.getOrDefault("owner",AttributeValue.fromS("")).s()))
   ? Optional.empty() : Optional.of(decode(item.get("payload").s()));
 }
 public List<Document> list() {
  var result = new ArrayList<Document>();
  var request=ScanRequest.builder().tableName(table).consistentRead(true);
  if(owner!=null) request.filterExpression("#o = :owner").expressionAttributeNames(Map.of("#o","owner"))
    .expressionAttributeValues(Map.of(":owner",AttributeValue.fromS(owner)));
  for (var page : db.scanPaginator(request.build()))
   for (var item : page.items()) {
    if(owner==null || owner.equals(item.getOrDefault("owner",AttributeValue.fromS("")).s())) result.add(decode(item.get("payload").s()));
   }
  result.sort(Comparator.comparing(Document::creadoEn).reversed()); return result;
 }
 public boolean replace(Document previous, Document next) {
  try {
   // Update only payload: stream/SQS workers must preserve the immutable owner attribute.
   db.updateItem(UpdateItemRequest.builder().tableName(table).key(key(next.documentId())).updateExpression("SET #p = :next")
     .conditionExpression("#p = :old") .expressionAttributeNames(Map.of("#p","payload"))
     .expressionAttributeValues(Map.of(":old",AttributeValue.fromS(encode(previous)),":next",AttributeValue.fromS(encode(next)))).build());
   return true;
  } catch (ConditionalCheckFailedException e) { return false; }
 }
 private String fileKey(String id, String ext) { LocalStore.checkId(id); LocalStore.checkExtension(ext); return id + "/" + ext; }
 public void putFile(String id, String ext, byte[] bytes) {
  s3.putObject(PutObjectRequest.builder().bucket(bucket).key(fileKey(id,ext))
   .contentType(ext.equals("pdf") ? "application/pdf" : "application/xml")
   .serverSideEncryption(ServerSideEncryption.AES256).build(), RequestBody.fromBytes(bytes));
 }
 public byte[] getFile(String id, String ext) {
  return s3.getObjectAsBytes(GetObjectRequest.builder().bucket(bucket).key(fileKey(id,ext)).build()).asByteArray();
 }
 public String downloadUrl(String id, String ext) {
  return signer.presignGetObject(r -> r.signatureDuration(Duration.ofMinutes(5)).getObjectRequest(g -> g.bucket(bucket)
   .key(fileKey(id,ext)).responseContentDisposition("attachment; filename=\"" + id + "." + ext + "\""))).url().toString();
 }
}
