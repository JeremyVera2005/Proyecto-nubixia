package pe.nubixia.comprobantes_serverless;
import com.amazonaws.services.lambda.runtime.*;
import com.amazonaws.services.lambda.runtime.events.*;
import java.util.*;
public class ApiHandler implements RequestHandler<APIGatewayProxyRequestEvent,APIGatewayProxyResponseEvent> {
 private ApiRouter router;
 static String authenticatedUser(APIGatewayProxyRequestEvent event) {
  var context=event.getRequestContext();
  if(context==null || context.getAuthorizer()==null) return null;
  Object claims=context.getAuthorizer().get("claims");
  if(!(claims instanceof Map<?,?> values)) return null;
  Object sub=values.get("sub");
  return sub instanceof String value && value.matches("[a-zA-Z0-9-]{1,128}") ? value : null;
 }
 public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent event,Context context) {
  var asset=StaticWeb.serve(event.getHttpMethod(),event.getPath());if(asset!=null)return asset;
  if(router==null)router=new ApiRouter(new InvoiceService(new AwsStore()));
  String body=event.getBody();
  if(Boolean.TRUE.equals(event.getIsBase64Encoded()) && body!=null)
   body=new String(Base64.getDecoder().decode(body),java.nio.charset.StandardCharsets.UTF_8);
  ApiRouter requestRouter=router;
  if("true".equals(System.getenv("AUTH_REQUIRED")) && !"/health".equals(event.getPath())) {
   String user=authenticatedUser(event);
   if(user==null) return new APIGatewayProxyResponseEvent().withStatusCode(401)
    .withHeaders(Map.of("Content-Type","application/json","Cache-Control","no-store"))
    .withBody("{\"mensaje\":\"Inicia sesión para continuar\"}");
   requestRouter=new ApiRouter(new InvoiceService(new AwsStore(user)));
  }
  var r=requestRouter.route(event.getHttpMethod(),event.getPath(),body);
  var headers=new HashMap<>(r.headers());
  headers.put("Access-Control-Allow-Origin",System.getenv().getOrDefault("CORS_ORIGIN","http://localhost:4200"));
  headers.put("X-Content-Type-Options","nosniff");
  return new APIGatewayProxyResponseEvent().withStatusCode(r.status()).withHeaders(headers).withBody(r.body()).withIsBase64Encoded(r.binary());
 }
}
