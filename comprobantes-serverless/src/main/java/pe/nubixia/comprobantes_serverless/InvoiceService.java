package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.time.Instant;
import java.util.*;
import org.slf4j.*;

public final class InvoiceService {
 private static final Logger log=LoggerFactory.getLogger(InvoiceService.class);
 private final Store store;
 private final FilesGenerator generator;
 public InvoiceService(Store store) { this(store,new FilesGenerator()); }
 public InvoiceService(Store store,FilesGenerator generator) { this.store=store; this.generator=generator; }
 public record Receipt(Document document, boolean duplicado) {}
 public Receipt receive(Invoice input) {
  Invoice i=validate(input);
  String id=hash(store.namespace()+i.rucEmisor()+"|"+i.serie()+"|"+i.numero());
  // Numeric normalization prevents 1.0 / 1.00 from causing spurious duplicate conflicts.
  var normalized=i.items().stream().map(v -> new Item(v.descripcion().strip(),v.cantidad().stripTrailingZeros(),v.precioUnitario().stripTrailingZeros())).toList();
  i=new Invoice(i.rucEmisor(),i.cliente(),i.fecha(),i.serie(),i.numero(),normalized,i.subtotal(),i.igv(),i.total());
  String fingerprint=hash(encode(i)), now=Instant.now().toString();
  Document d=new Document(id,fingerprint,i,"RECIBIDO",now,now,List.of(new Event("RECIBIDO",now,"Solicitud validada y registrada")),null,0);
  boolean created=store.create(d);
  if(!created) {
   d=get(id);
   if(!fingerprint.equals(d.fingerprint())) throw new ApiException(409,"Ya existe la misma serie y número con datos distintos");
  }
  log.info("documentId={} event=recepcion duplicado={}",id,!created);
  return new Receipt(d,!created);
 }
 public Document get(String id) { return store.find(id).orElseThrow(() -> new ApiException(404,"Comprobante no encontrado")); }
 public List<Document> list() { return store.list(); }
 public void process(String id) {
  Document old=get(id);
  if(Set.of("ACEPTADO","RECHAZADO").contains(old.estado())) return;
  if(old.estado().equals("PROCESANDO") && old.leaseUntil()>Instant.now().getEpochSecond())
   throw new IllegalStateException("Procesamiento ya adquirido; reintentar después");
  Document working=old.transition("PROCESANDO","Generando XML y PDF",Instant.now().getEpochSecond()+90);
  if(!store.replace(old,working)) throw new IllegalStateException("Conflicto de procesamiento; reintentar");
  log.info("documentId={} event=PROCESANDO",id);
  try {
   validate(working.comprobante());
   store.putFile(id,"xml",generator.xml(working)); store.putFile(id,"pdf",generator.pdf(working));
   if(!store.replace(working,working.transition("ACEPTADO","XML y PDF disponibles. Simulación académica.",0)))
    throw new IllegalStateException("No se pudo confirmar el procesamiento");
   log.info("documentId={} event=ACEPTADO",id);
  } catch(ApiException e) {
   store.replace(working,working.transition("RECHAZADO",e.getMessage(),0));
   log.warn("documentId={} event=RECHAZADO",id);
  } catch(Exception e) {
   log.error("documentId={} event=ERROR",id,e);
   store.replace(working,working.transition("ERROR","Fallo técnico al generar archivos; se reintentará",0));
   throw new IllegalStateException("Error procesando "+id,e);
  }
 }
 public Map<String,Object> view(Document d) {
  var v=new LinkedHashMap<String,Object>();
  v.put("documentId",d.documentId()); v.put("estado",d.estado()); v.put("comprobante",d.comprobante());
  v.put("creadoEn",d.creadoEn()); v.put("actualizadoEn",d.actualizadoEn()); v.put("historial",d.historial()); v.put("error",d.error());
  v.put("archivosDisponibles",d.estado().equals("ACEPTADO")); return v;
 }
 public String downloadUrl(String id,String ext) {
  if(!get(id).estado().equals("ACEPTADO")) throw new ApiException(409,"Los archivos aún no están disponibles");
  LocalStore.checkExtension(ext); return store.downloadUrl(id,ext);
 }
 public byte[] file(String id,String ext) {
  if(!get(id).estado().equals("ACEPTADO")) throw new ApiException(409,"Los archivos aún no están disponibles");
  return store.getFile(id,ext);
 }
}
