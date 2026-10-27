package pe.nubixia.comprobantes_serverless;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Public, allowlisted SPA assets. Business routes still require Cognito at API Gateway. */
final class StaticWeb {
 static String asset(String path) {
  if("/".equals(path) || "/index.html".equals(path)) return "index.html";
  if(path!=null && path.matches("/(?:main-[A-Za-z0-9]+\\.js|styles-[A-Za-z0-9]+\\.css|nubixia-logo\\.png|favicon\\.ico)")) return path.substring(1);
  return null;
 }
 static APIGatewayProxyResponseEvent serve(String method,String path) {
  if(!"GET".equals(method)) return null;
  if("/config.json".equals(path)) {
   String pool=System.getenv("COGNITO_USER_POOL_ID"),client=System.getenv("COGNITO_CLIENT_ID");
   if(pool==null || client==null) return response(503,"application/json","{\"mensaje\":\"Configuración de acceso pendiente\"}",false,"no-store");
   return response(200,"application/json",Domain.encode(Map.of("apiUrl","/demo","cloudMode",true,
    "auth",Map.of("region","us-east-2","userPoolId",pool,"clientId",client))),false,"no-store");
  }
  String file=asset(path);if(file==null)return null;
  try(var input=StaticWeb.class.getResourceAsStream("/web/"+file)) {
   if(input==null)return response(404,"text/plain; charset=utf-8","Archivo no encontrado",false,"no-store");
   byte[] bytes=input.readAllBytes();boolean binary=file.endsWith(".png")||file.endsWith(".ico");
   String type=file.endsWith(".js")?"text/javascript; charset=utf-8":file.endsWith(".css")?"text/css; charset=utf-8":file.endsWith(".png")?"image/png":file.endsWith(".ico")?"image/x-icon":"text/html; charset=utf-8";
   String cache=file.startsWith("main-")||file.startsWith("styles-")?"public, max-age=31536000, immutable":"no-cache";
   return response(200,type,binary?Base64.getEncoder().encodeToString(bytes):new String(bytes,StandardCharsets.UTF_8),binary,cache);
  }catch(IOException e){throw new IllegalStateException("No se pudo leer el frontend empaquetado",e);}
 }
 private static APIGatewayProxyResponseEvent response(int code,String type,String body,boolean binary,String cache) {
  return new APIGatewayProxyResponseEvent().withStatusCode(code).withHeaders(Map.of("Content-Type",type,"Cache-Control",cache,
   "X-Content-Type-Options","nosniff","X-Frame-Options","DENY","Referrer-Policy","no-referrer",
   "Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https://cognito-idp.us-east-2.amazonaws.com https://*.s3.us-east-2.amazonaws.com https://*.s3.amazonaws.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"))
   .withBody(body).withIsBase64Encoded(binary);
 }
}
