package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;

class InvoiceServiceTest {
 @TempDir Path dir;
 SqlStore store; InvoiceService service; org.springframework.jdbc.core.JdbcTemplate jdbc;
  @BeforeEach void setup() {
  var ds=new org.springframework.jdbc.datasource.DriverManagerDataSource("jdbc:h2:file:"+dir.resolve("nubixia"),"sa","");
  new org.springframework.jdbc.datasource.init.ResourceDatabasePopulator(
   new org.springframework.core.io.ClassPathResource("db/migration/V1__comprobantes.sql")).execute(ds);
  jdbc=new org.springframework.jdbc.core.JdbcTemplate(ds);
  store=new SqlStore(jdbc,new org.springframework.transaction.support.TransactionTemplate(new org.springframework.jdbc.datasource.DataSourceTransactionManager(ds)));
  service=new InvoiceService(store);
 }
 static Invoice invoice(String n) {
  return new Invoice("20123456789","Cliente & <Prueba>","2026-10-25","F001",n,
   List.of(new Item("Servicio de prueba",new BigDecimal("2"),new BigDecimal("50.00"))),
   new BigDecimal("100.00"),new BigDecimal("18.00"),new BigDecimal("118.00"));
 }
 @Test void technicalFailureIsRecordedAndCanRetry() {
  Store failing=org.mockito.Mockito.spy(store);
  org.mockito.Mockito.doThrow(new IllegalStateException("S3 temporal")).doCallRealMethod()
   .when(failing).putFile(org.mockito.ArgumentMatchers.anyString(),org.mockito.ArgumentMatchers.eq("xml"),org.mockito.ArgumentMatchers.any(byte[].class));
  var s=new InvoiceService(failing); String id=s.receive(invoice("1")).document().documentId();
  assertThrows(IllegalStateException.class,()->s.process(id));
  assertEquals("ERROR",s.get(id).estado()); assertNotNull(s.get(id).error());
  s.process(id); assertEquals("ACEPTADO",s.get(id).estado());
  assertEquals(List.of("RECIBIDO","PROCESANDO","ERROR","PROCESANDO","ACEPTADO"),s.get(id).historial().stream().map(Event::estado).toList());
 }
 @Test void sqlTablesContainItemsEventsAndFiles() {
  String id=service.receive(invoice("1")).document().documentId(); service.process(id);
  assertEquals(1,jdbc.queryForObject("SELECT COUNT(*) FROM comprobantes",Integer.class));
  assertEquals(1,jdbc.queryForObject("SELECT COUNT(*) FROM comprobante_items",Integer.class));
  assertEquals(3,jdbc.queryForObject("SELECT COUNT(*) FROM comprobante_eventos",Integer.class));
  assertEquals(2,jdbc.queryForObject("SELECT COUNT(*) FROM comprobante_archivos",Integer.class));
  assertEquals("ACEPTADO",jdbc.queryForObject("SELECT estado FROM comprobantes WHERE document_id=?",String.class,id));
 }
 @Test void importsLegacyJsonAndFilesWithoutDuplicates() {
  Path legacy=dir.resolve("legacy");
  var oldStore=new LocalStore(legacy); var oldService=new InvoiceService(oldStore);
  String id=oldService.receive(invoice("1")).document().documentId(); oldService.process(id);
  assertEquals(1,store.importLegacy(legacy)); assertEquals(0,store.importLegacy(legacy));
  assertEquals("ACEPTADO",service.get(id).estado());
  assertArrayEquals(oldStore.getFile(id,"pdf"),store.getFile(id,"pdf"));
  assertEquals(3,jdbc.queryForObject("SELECT COUNT(*) FROM comprobante_eventos",Integer.class));
  assertTrue(Files.exists(legacy.resolve("documents").resolve(id+".json")));
 }
 @Test void incompleteLegacyFilesDoNotCreateAcceptedSqlRecord() throws Exception {
  Path legacy=dir.resolve("legacy");
  var oldStore=new LocalStore(legacy); var oldService=new InvoiceService(oldStore);
  String id=oldService.receive(invoice("1")).document().documentId(); oldService.process(id);
  // Simulate an absent artifact without changing the source document.
  Files.move(legacy.resolve("files").resolve(id+".pdf"),legacy.resolve("files").resolve(id+".pdf.backup"));
  assertThrows(IllegalStateException.class,()->store.importLegacy(legacy));
  assertTrue(store.find(id).isEmpty());
 }
 @Test void validatesTotalsAndDates() {
  var i=invoice("1");
  assertEquals("118.00",validate(i).total().toPlainString());
  assertThrows(ApiException.class,()->validate(new Invoice(i.rucEmisor(),i.cliente(),"2026-02-30",i.serie(),i.numero(),i.items(),i.subtotal(),i.igv(),i.total())));
  assertThrows(ApiException.class,()->validate(new Invoice(i.rucEmisor(),i.cliente(),i.fecha(),i.serie(),i.numero(),i.items(),i.subtotal(),i.igv(),BigDecimal.ZERO)));
  assertThrows(ApiException.class,()->validate(new Invoice("123",i.cliente(),i.fecha(),i.serie(),i.numero(),i.items(),i.subtotal(),i.igv(),i.total())));
  assertThrows(ApiException.class,()->validate(new Invoice(i.rucEmisor()," ",i.fecha(),i.serie(),i.numero(),i.items(),i.subtotal(),i.igv(),i.total())));
  assertThrows(ApiException.class,()->validate(new Invoice(i.rucEmisor(),i.cliente(),i.fecha(),i.serie(),i.numero(),List.of(),i.subtotal(),i.igv(),i.total())));
 }
 @Test void persistsHistoryAndGeneratesReadableFiles() throws Exception {
  String id=service.receive(invoice("1")).document().documentId();
  assertEquals("RECIBIDO",service.get(id).estado());
  service.process(id);
  assertEquals("ACEPTADO",service.get(id).estado());
  assertEquals(List.of("RECIBIDO","PROCESANDO","ACEPTADO"),service.get(id).historial().stream().map(Event::estado).toList());
  var factory=DocumentBuilderFactory.newInstance();
  var xml=factory.newDocumentBuilder().parse(new java.io.ByteArrayInputStream(service.file(id,"xml")));
  assertEquals("Cliente & <Prueba>",xml.getElementsByTagName("Cliente").item(0).getTextContent());
  try(var pdf=Loader.loadPDF(service.file(id,"pdf"))) {
   assertEquals(1,pdf.getNumberOfPages());
   String text=new PDFTextStripper().getText(pdf);
   assertTrue(text.contains("118.00")); assertTrue(text.contains("SIN VALIDEZ TRIBUTARIA"));
  }
  assertEquals("ACEPTADO",new SqlStore(jdbc,new org.springframework.transaction.support.TransactionTemplate(new org.springframework.jdbc.datasource.DataSourceTransactionManager(jdbc.getDataSource()))).find(id).orElseThrow().estado());
  byte[] original=service.file(id,"pdf"); service.process(id);
  assertArrayEquals(original,service.file(id,"pdf")); assertEquals(3,service.get(id).historial().size());
 }
 @Test void duplicateAndConflict() {
  var first=service.receive(invoice("1")); assertFalse(first.duplicado());
  assertTrue(service.receive(invoice("01")).duplicado()); assertEquals(1,store.list().size());
  var i=invoice("1");
  var ex=assertThrows(ApiException.class,()->service.receive(new Invoice(i.rucEmisor(),"Otro cliente",i.fecha(),i.serie(),i.numero(),i.items(),i.subtotal(),i.igv(),i.total())));
  assertEquals(409,ex.status);
 }
 @Test void twentyConcurrentRequestsAreNotLost() throws Exception {
  var pool=Executors.newFixedThreadPool(20);
  try {
   var tasks=new ArrayList<Callable<String>>();
   for(int n=1;n<=20;n++) { String number=String.valueOf(n); tasks.add(()-> {
    String id=service.receive(invoice(number)).document().documentId(); service.process(id); return id;
   }); }
   var ids=new HashSet<String>();
   for(var future:pool.invokeAll(tasks)) ids.add(future.get(15,TimeUnit.SECONDS));
   assertEquals(20,ids.size()); assertEquals(20,store.list().size());
   for(String id:ids) { assertEquals("ACEPTADO",service.get(id).estado()); assertTrue(service.file(id,"xml").length>0); assertTrue(service.file(id,"pdf").length>0); }
  } finally { pool.shutdownNow(); }
 }
 @Test void concurrentDuplicatesCreateOneRecord() throws Exception {
  var pool=Executors.newFixedThreadPool(20);
  try {
   var tasks=new ArrayList<Callable<InvoiceService.Receipt>>();
   for(int n=0;n<20;n++) tasks.add(()->service.receive(invoice("1")));
   long created=0;
   for(var result:pool.invokeAll(tasks)) if(!result.get().duplicado()) created++;
   assertEquals(1,created); assertEquals(1,store.list().size());
  } finally { pool.shutdownNow(); }
 }
 @Test void downloadRequiresAcceptedStateAndSafePaths() {
  var id=service.receive(invoice("1")).document().documentId();
  assertEquals(409,assertThrows(ApiException.class,()->service.file(id,"pdf")).status);
  assertEquals(404,assertThrows(ApiException.class,()->service.get("../anything")).status);
 }
 @Test void apiRoutesAndMalformedJson() {
  var api=new ApiRouter(service);
  assertEquals(400,api.route("POST","/comprobantes","{").status());
  var response=api.route("POST","/comprobantes",encode(invoice("1")));
  assertEquals(202,response.status());
  assertEquals(200,api.route("GET","/comprobantes","").status());
  assertEquals(404,api.route("GET","/not-found","").status());
 }
 @Test void multipagePdfSupportsHundredItems() throws Exception {
  var i=invoice("2"); var items=new ArrayList<Item>();
  for(int n=0;n<100;n++) items.add(new Item("Línea "+n+" "+"detalle ".repeat(20),BigDecimal.ONE,BigDecimal.ONE));
  var large=new Invoice(i.rucEmisor(),i.cliente(),i.fecha(),i.serie(),i.numero(),items,i.subtotal(),i.igv(),i.total());
  String id=service.receive(large).document().documentId(); service.process(id);
  try(var pdf=Loader.loadPDF(service.file(id,"pdf"))) { assertTrue(pdf.getNumberOfPages()>1); assertTrue(new PDFTextStripper().getText(pdf).contains("TOTAL: S/ 118.00")); }
 }
}