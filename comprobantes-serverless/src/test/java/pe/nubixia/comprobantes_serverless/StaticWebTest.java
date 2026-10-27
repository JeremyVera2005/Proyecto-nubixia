package pe.nubixia.comprobantes_serverless;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
class StaticWebTest {
 @Test void onlyAllowsBuildAssetsAndNeverBusinessDataOrTraversal() {
  assertEquals("index.html",StaticWeb.asset("/"));
  assertEquals("main-ABC123.js",StaticWeb.asset("/main-ABC123.js"));
  for(String path:new String[]{"/comprobantes","/../application.properties","/.env.aws.json","/application.properties","/web/../config.json","/main.js/../secret"})assertNull(StaticWeb.asset(path));
  assertNull(StaticWeb.serve("POST","/index.html"));
 }
 @Test void packagedHtmlAndImageHaveCorrectEncodingAndSecurityHeaders() {
  var html=StaticWeb.serve("GET","/");assertEquals(200,html.getStatusCode());assertFalse(html.getIsBase64Encoded());
  assertTrue(html.getBody().contains("<base href=\"/demo/\">"));
  assertEquals("nosniff",html.getHeaders().get("X-Content-Type-Options"));
  var logo=StaticWeb.serve("GET","/nubixia-logo.png");assertEquals(200,logo.getStatusCode());assertTrue(logo.getIsBase64Encoded());
 }
}
