package pe.nubixia.comprobantes_serverless;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.*;
import org.springframework.test.annotation.DirtiesContext;
import java.nio.file.Path;
import java.net.*;
import java.net.http.*;
import static org.junit.jupiter.api.Assertions.*;

@DirtiesContext(classMode=DirtiesContext.ClassMode.AFTER_CLASS)
@SpringBootTest(webEnvironment=SpringBootTest.WebEnvironment.RANDOM_PORT,properties={"nubixia.api-key=rate-test","nubixia.rate-limit=2"})
class RateLimitTest {
 @TempDir static Path data;
 @LocalServerPort int port;
 @DynamicPropertySource static void properties(DynamicPropertyRegistry r) { r.add("nubixia.data-dir",()->data.toString()); r.add("spring.datasource.url",()->"jdbc:h2:file:"+data.resolve("nubixia")); }
 @Test void thirdAuthenticatedRequestIsThrottledAndCorsPreflightWorks() throws Exception {
  var client=HttpClient.newHttpClient(); URI uri=URI.create("http://localhost:"+port+"/comprobantes");
  var options=HttpRequest.newBuilder(uri).method("OPTIONS",HttpRequest.BodyPublishers.noBody())
   .header("Origin","http://localhost:4200").header("Access-Control-Request-Method","POST").build();
  var preflight=client.send(options,HttpResponse.BodyHandlers.ofString());
  assertEquals(204,preflight.statusCode()); assertEquals("http://localhost:4200",preflight.headers().firstValue("Access-Control-Allow-Origin").orElse(""));
  var request=HttpRequest.newBuilder(uri).header("X-API-Key","rate-test").GET().build();
  assertEquals(200,client.send(request,HttpResponse.BodyHandlers.ofString()).statusCode());
  assertEquals(200,client.send(request,HttpResponse.BodyHandlers.ofString()).statusCode());
  var limited=client.send(request,HttpResponse.BodyHandlers.ofString());
  assertEquals(429,limited.statusCode()); assertEquals("60",limited.headers().firstValue("Retry-After").orElse(""));
 }
}