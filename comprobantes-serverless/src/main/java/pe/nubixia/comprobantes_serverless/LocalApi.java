package pe.nubixia.comprobantes_serverless;
import jakarta.annotation.PreDestroy;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import static pe.nubixia.comprobantes_serverless.Domain.*;

@Configuration
@EnableScheduling
class LocalConfiguration {
  @Bean
 @org.springframework.boot.sql.init.dependency.DependsOnDatabaseInitialization
 SqlStore store(org.springframework.jdbc.core.JdbcTemplate jdbc, org.springframework.transaction.PlatformTransactionManager manager,
   @Value("${nubixia.data-dir:./data}") String dir) {
  var store=new SqlStore(jdbc,new org.springframework.transaction.support.TransactionTemplate(manager));
  int imported=store.importLegacy(Path.of(dir));
  org.slf4j.LoggerFactory.getLogger(LocalConfiguration.class).info("database=H2 event=READY legacyImported={}",imported);
  return store;
 }
 @Bean InvoiceService service(SqlStore store) { return new InvoiceService(store); }
 @Bean ApiRouter router(InvoiceService service) { return new ApiRouter(service); }
 @Bean FilterRegistrationBean<Filter> security(@Value("${nubixia.api-key}") String key,
    @Value("${nubixia.cors-origin:http://localhost:4200}") String origin,
    @Value("${nubixia.rate-limit:120}") int limit) {
  if(key.isBlank()) throw new IllegalStateException("Configura NUBIXIA_API_KEY");
  var filter=new FilterRegistrationBean<Filter>();
  filter.setFilter(new Filter() {
   private long minute=-1; private int requests=0;
   private synchronized boolean allowed() {
    long now=Instant.now().getEpochSecond()/60;
    if(now!=minute) { minute=now; requests=0; } return ++requests<=limit;
   }
   public void doFilter(ServletRequest request,ServletResponse response,FilterChain chain) throws java.io.IOException,ServletException {
    var req=(HttpServletRequest)request; var res=(HttpServletResponse)response;
    String requestOrigin=req.getHeader("Origin");
    if(origin.equals(requestOrigin)) {
     res.setHeader("Access-Control-Allow-Origin",origin); res.setHeader("Vary","Origin");
     res.setHeader("Access-Control-Allow-Headers","Content-Type,X-API-Key");
     res.setHeader("Access-Control-Allow-Methods","GET,POST,OPTIONS");
    }
    res.setHeader("X-Content-Type-Options","nosniff"); res.setHeader("Cache-Control","no-store");
    if(req.getMethod().equals("OPTIONS")) { res.setStatus(204); return; }
    if(req.getRequestURI().equals("/health")) { chain.doFilter(request,response); return; }
        if(req.getRequestURI().equals("/h2-console") || req.getRequestURI().startsWith("/h2-console/")) {
     if(!Set.of("127.0.0.1","::1","0:0:0:0:0:0:0:1").contains(req.getRemoteAddr())) {
      res.setStatus(403); return;
     }
     String expected="admin:"+key, credentials="";
     String auth=Objects.toString(req.getHeader("Authorization"),"");
     try { if(auth.startsWith("Basic ")) credentials=new String(Base64.getDecoder().decode(auth.substring(6)),StandardCharsets.UTF_8); }
     catch(IllegalArgumentException ignored) {}
     if(!MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8),credentials.getBytes(StandardCharsets.UTF_8))) {
      res.setHeader("WWW-Authenticate","Basic realm=\"Nubixia SQL\", charset=\"UTF-8\""); res.setStatus(401); return;
     }
     chain.doFilter(request,response); return;
    }
    String supplied=Objects.toString(req.getHeader("X-API-Key"),"");
    if(!MessageDigest.isEqual(key.getBytes(StandardCharsets.UTF_8),supplied.getBytes(StandardCharsets.UTF_8))) {
     res.setStatus(401); res.setContentType("application/json;charset=UTF-8"); res.getWriter().write("{\"mensaje\":\"API key ausente o inválida\"}"); return;
    }
    if(!allowed()) {
     res.setStatus(429); res.setHeader("Retry-After","60"); res.setContentType("application/json;charset=UTF-8");
     res.getWriter().write("{\"mensaje\":\"Límite de solicitudes por minuto alcanzado\"}"); return;
    }
    chain.doFilter(request,response);
   }
  });
  filter.addUrlPatterns("/*"); return filter;
 }
}
@RestController
class LocalApi {
 private final ApiRouter router;
 LocalApi(ApiRouter router) { this.router=router; }
 @RequestMapping(value={"/health","/comprobantes","/comprobantes/**"},method={RequestMethod.GET,RequestMethod.POST})
 ResponseEntity<byte[]> handle(HttpServletRequest req,@RequestBody(required=false) String body) {
  var r=router.route(req.getMethod(),req.getRequestURI(),body);
  var headers=new HttpHeaders(); r.headers().forEach(headers::set);
  return new ResponseEntity<>(r.binary()?Base64.getDecoder().decode(r.body()):r.body().getBytes(StandardCharsets.UTF_8),headers,HttpStatusCode.valueOf(r.status()));
 }
}
@org.springframework.stereotype.Component
class LocalWorker {
 private final SqlStore store; private final InvoiceService service;
 private final ExecutorService workers=Executors.newFixedThreadPool(4);
 private final Set<String> scheduled=ConcurrentHashMap.newKeySet();
 LocalWorker(SqlStore store,InvoiceService service) { this.store=store; this.service=service; }
 @Scheduled(fixedDelay=1000)
 void poll() {
  for(var d:store.list()) {
   boolean retry=d.estado().equals("RECIBIDO") || d.estado().equals("ERROR") ||
    (d.estado().equals("PROCESANDO") && d.leaseUntil()<Instant.now().getEpochSecond());
   long errors=d.historial().stream().filter(e->e.estado().equals("ERROR")).count();
   if(retry && errors<5 && scheduled.add(d.documentId())) workers.submit(()-> {
    try { service.process(d.documentId()); }
    catch(Exception e) { org.slf4j.LoggerFactory.getLogger(LocalWorker.class).error("documentId={} event=RETRY",d.documentId(),e); }
    finally { scheduled.remove(d.documentId()); }
   });
  }
 }
 @PreDestroy void stop() throws InterruptedException { workers.shutdown(); workers.awaitTermination(30,TimeUnit.SECONDS); }
}