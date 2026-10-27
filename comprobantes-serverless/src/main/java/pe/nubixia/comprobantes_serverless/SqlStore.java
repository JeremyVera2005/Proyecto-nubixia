package pe.nubixia.comprobantes_serverless;

import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.util.*;
import java.nio.file.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.transaction.support.TransactionTemplate;

/** Persistent SQL adapter. Updates of document, items and history share one transaction. */
public class SqlStore implements Store {
 private final JdbcTemplate jdbc;
 private final TransactionTemplate tx;
 public SqlStore(JdbcTemplate jdbc, TransactionTemplate tx) { this.jdbc=jdbc; this.tx=tx; }

 public boolean create(Document d) {
  try { return Boolean.TRUE.equals(tx.execute(s -> { insert(d); return true; })); }
  catch(DuplicateKeyException e) { return false; }
 }
 private void insert(Document d) {
  var i=d.comprobante(); String payload=encode(d);
  jdbc.update("INSERT INTO comprobantes (document_id,fingerprint,revision,ruc_emisor,cliente,fecha,serie,numero,subtotal,igv,total,estado,creado_en,actualizado_en,error,payload) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
   d.documentId(),d.fingerprint(),hash(payload),i.rucEmisor(),i.cliente(),java.sql.Date.valueOf(i.fecha()),
   i.serie(),i.numero(),i.subtotal(),i.igv(),i.total(),d.estado(),d.creadoEn(),d.actualizadoEn(),d.error(),payload);
  int position=0;
  for(var item:i.items())
   jdbc.update("INSERT INTO comprobante_items (document_id,posicion,descripcion,cantidad,precio_unitario) VALUES (?,?,?,?,?)",
    d.documentId(),position++,item.descripcion(),item.cantidad(),item.precioUnitario());
  history(d);
 }
 private void history(Document d) {
  jdbc.update("DELETE FROM comprobante_eventos WHERE document_id=?",d.documentId());
  int position=0;
  for(var e:d.historial())
   jdbc.update("INSERT INTO comprobante_eventos (document_id,posicion,estado,fecha,detalle) VALUES (?,?,?,?,?)",
    d.documentId(),position++,e.estado(),e.fecha(),e.detalle());
 }
 public Optional<Document> find(String id) {
  LocalStore.checkId(id);
  return jdbc.query("SELECT payload FROM comprobantes WHERE document_id=?",(rs,n)->decode(rs.getString(1)),id).stream().findFirst();
 }
 public List<Document> list() {
  return jdbc.query("SELECT payload FROM comprobantes ORDER BY creado_en DESC, document_id",(rs,n)->decode(rs.getString(1)));
 }
 public boolean replace(Document previous,Document next) {
  if(!previous.documentId().equals(next.documentId())) throw new IllegalArgumentException("No se puede cambiar el documentId");
  return Boolean.TRUE.equals(tx.execute(s -> {
   String payload=encode(next);
   int changed=jdbc.update("UPDATE comprobantes SET revision=?,estado=?,actualizado_en=?,error=?,payload=? WHERE document_id=? AND revision=?",
    hash(payload),next.estado(),next.actualizadoEn(),next.error(),payload,next.documentId(),hash(encode(previous)));
   if(changed==0) return false;
   history(next); return true;
  }));
 }
 public void putFile(String id,String ext,byte[] bytes) {
  LocalStore.checkId(id); LocalStore.checkExtension(ext);
  jdbc.update("MERGE INTO comprobante_archivos (document_id,extension,contenido) KEY(document_id,extension) VALUES (?,?,?)",id,ext,bytes);
 }
 public byte[] getFile(String id,String ext) {
  LocalStore.checkId(id); LocalStore.checkExtension(ext);
  return jdbc.query("SELECT contenido FROM comprobante_archivos WHERE document_id=? AND extension=?",
   (rs,n)->rs.getBytes(1),id,ext).stream().findFirst().orElseThrow(()->new ApiException(404,"Archivo no encontrado"));
 }
 /** Import the legacy JSON and both files atomically, without modifying the source. */
 public int importLegacy(Path root) {
  Path documents=root.resolve("documents");
  if(!Files.isDirectory(documents)) return 0;
  int imported=0;
  try(var paths=Files.list(documents)) {
   for(Path p:paths.filter(v->v.toString().endsWith(".json")).sorted().toList()) {
    Document d=decode(Files.readString(p));
    if(find(d.documentId()).isPresent()) continue;
    byte[] xml=null,pdf=null;
    if(d.estado().equals("ACEPTADO")) {
     xml=Files.readAllBytes(root.resolve("files").resolve(d.documentId()+".xml"));
     pdf=Files.readAllBytes(root.resolve("files").resolve(d.documentId()+".pdf"));
    }
    final byte[] xmlBytes=xml,pdfBytes=pdf;
    try {
     tx.executeWithoutResult(s -> {
      insert(d);
      if(xmlBytes!=null) { putFile(d.documentId(),"xml",xmlBytes); putFile(d.documentId(),"pdf",pdfBytes); }
     });
     imported++;
    } catch(DuplicateKeyException e) { /* Concurrent importer already committed this document. */ }
   }
  } catch(java.io.IOException e) { throw new IllegalStateException("No se pudo migrar el respaldo JSON. Se conserva el original.",e); }
  return imported;
 }
}
