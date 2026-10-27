package pe.nubixia.comprobantes_serverless;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import java.nio.file.Path;
import java.net.*;
import java.net.http.*;
import static org.junit.jupiter.api.Assertions.*;
import static pe.nubixia.comprobantes_serverless.Domain.*;

@org.springframework.test.annotation.DirtiesContext(classMode=org.springframework.test.annotation.DirtiesContext.ClassMode.AFTER_CLASS)
@SpringBootTest(webEnvironment=SpringBootTest.WebEnvironment.RANDOM_PORT)
class ComprobantesServerlessApplicationTests {
 @TempDir static Path data;
 @LocalServerPort int port;
 @DynamicPropertySource static void properties(DynamicPropertyRegistry r) {
  r.add("nubixia.data-dir",()->data.toString()); r.add("spring.datasource.url",()->"jdbc:h2:file:"+data.resolve("nubixia")); r.add("nubixia.api-key",()->"test-key"); r.add("nubixia.rate-limit",()->1000);
 }
 HttpResponse<byte[]> call(String method,String path,String body,boolean auth) throws Exception {
  var b=HttpRequest.newBuilder(URI.create("http://localhost:"+port+path));
  if(auth) b.header("X-API-Key","test-key");
  if(body!=null) b.header("Content-Type","application/json");
  b.method(method,body==null?HttpRequest.BodyPublishers.noBody():HttpRequest.BodyPublishers.ofString(body));
  return HttpClient.newHttpClient().send(b.build(),HttpResponse.BodyHandlers.ofByteArray());
 }
 @Test void databaseConsoleRequiresLocalBasicAuthentication() throws Exception {
  assertEquals(401,call("GET","/h2-console/",null,false).statusCode());
  String credentials=java.util.Base64.getEncoder().encodeToString("admin:test-key".getBytes(java.nio.charset.StandardCharsets.UTF_8));
  var request=HttpRequest.newBuilder(URI.create("http://localhost:"+port+"/h2-console/")).header("Authorization","Basic "+credentials).GET().build();
  var response=HttpClient.newHttpClient().send(request,HttpResponse.BodyHandlers.ofString());
  assertTrue(response.statusCode()==200 || response.statusCode()==302,"La consola debe estar registrada");
 }
 @Test void authenticatedHttpFlow() throws Exception {
  assertEquals(401,call("GET","/comprobantes",null,false).statusCode());
  assertEquals(200,call("GET","/health",null,false).statusCode());
  var response=call("POST","/comprobantes",encode(InvoiceServiceTest.invoice("1")),true);
  assertEquals(202,response.statusCode());
  String id=JSON.readTree(response.body()).get("documentId").asText();
  boolean accepted=false;
  for(int n=0;n<60;n++) {
   var status=call("GET","/comprobantes/"+id,null,true);
   if(JSON.readTree(status.body()).get("estado").asText().equals("ACEPTADO")) { accepted=true; break; }
   Thread.sleep(100);
  }
  assertTrue(accepted,"El worker asíncrono debe finalizar en menos de 6 segundos");
  assertEquals(200,call("POST","/comprobantes",encode(InvoiceServiceTest.invoice("1")),true).statusCode());
  var pdf=call("GET","/comprobantes/"+id+"/archivos/pdf",null,true);
  assertEquals(200,pdf.statusCode()); assertTrue(new String(pdf.body(),0,4).startsWith("%PDF"));
  assertEquals(200,call("GET","/comprobantes/"+id+"/archivos/xml",null,true).statusCode());
 }
}