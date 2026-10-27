package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.util.*;
import org.slf4j.*;

public final class ApiRouter {
 private static final Logger log=LoggerFactory.getLogger(ApiRouter.class);
 private final InvoiceService service;
 public ApiRouter(InvoiceService service) { this.service=service; }
 public record Response(int status, Map<String,String> headers, String body, boolean binary) {}
 private Response json(int code,Object value) { return new Response(code,Map.of("Content-Type","application/json; charset=utf-8","Cache-Control","no-store"),encode(value),false); }
 public Response route(String method,String path,String body) {
  try {
   if(method.equals("GET") && path.equals("/health")) return json(200,Map.of("status","UP","modo",System.getenv("TABLE_NAME")==null?"local":"aws","academico",true));
   if(path.equals("/comprobantes")) {
    if(method.equals("POST")) {
     if(body==null || body.isBlank()) throw new ApiException(400,"El cuerpo JSON es obligatorio");
     if(body.length()>200000) throw new ApiException(413,"Solicitud demasiado grande");
     Invoice input;
     try { input=JSON.readValue(body,Invoice.class); }
     catch(Exception e) { throw new ApiException(400,"JSON inválido o tipos de datos incorrectos"); }
     var receipt=service.receive(input); var result=service.view(receipt.document());
     result.put("duplicado",receipt.duplicado()); return json(receipt.duplicado()?200:202,result);
    }
    if(method.equals("GET")) return json(200,Map.of("items",service.list().stream().map(service::view).toList()));
   }
   String[] parts=path.split("/");
   if(method.equals("GET") && parts.length>=3 && parts[1].equals("comprobantes")) {
    if(parts.length==3) return json(200,service.view(service.get(parts[2])));
    if(parts.length==5 && parts[3].equals("archivos")) {
     String url=service.downloadUrl(parts[2],parts[4]);
     if(url!=null) return json(200,Map.of("url",url,"expiraEnSegundos",300));
     byte[] data=service.file(parts[2],parts[4]);
     return new Response(200,Map.of("Content-Type",parts[4].equals("pdf")?"application/pdf":"application/xml; charset=utf-8",
       "Content-Disposition","attachment; filename=\""+parts[2]+"."+parts[4]+"\"","Cache-Control","no-store"),Base64.getEncoder().encodeToString(data),true);
    }
   }
   throw new ApiException(404,"Ruta no encontrada");
  } catch(ApiException e) { return json(e.status,Map.of("mensaje",e.getMessage())); }
  catch(Exception e) {
   String trace=UUID.randomUUID().toString(); log.error("requestId={} event=API_ERROR",trace,e);
   return json(500,Map.of("mensaje","Error técnico. Consulta los logs con el identificador de solicitud.","requestId",trace));
  }
 }
}