package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.nio.file.*;
import java.util.*;
import java.io.IOException;

/** Local development adapter. A single JVM owns the data directory. */
public final class LocalStore implements Store {
 private final Path root;
 public LocalStore(Path root) {
  this.root = root.toAbsolutePath().normalize();
  try { Files.createDirectories(this.root.resolve("documents")); Files.createDirectories(this.root.resolve("files")); }
  catch (IOException e) { throw new IllegalStateException(e); }
 }
 private Path record(String id) { checkId(id); return root.resolve("documents").resolve(id + ".json"); }
 static void checkId(String id) { if (id == null || !id.matches("[a-f0-9]{64}")) throw new ApiException(404,"Comprobante no encontrado"); }
 static void checkExtension(String ext) { if (!Set.of("xml","pdf").contains(ext)) throw new ApiException(404,"Archivo no encontrado"); }
 private void atomic(Path target, byte[] bytes) {
  try {
   Path temp = Files.createTempFile(target.getParent(), ".write-", ".tmp");
   try { Files.write(temp, bytes); Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
   finally { Files.deleteIfExists(temp); }
  } catch (IOException e) { throw new IllegalStateException("No se pudo guardar en disco", e); }
 }
 public synchronized boolean create(Document d) {
  if (Files.exists(record(d.documentId()))) return false;
  atomic(record(d.documentId()), encode(d).getBytes(java.nio.charset.StandardCharsets.UTF_8)); return true;
 }
 public synchronized Optional<Document> find(String id) {
  try { Path p = record(id); return Files.exists(p) ? Optional.of(decode(Files.readString(p))) : Optional.empty(); }
  catch (IOException e) { throw new IllegalStateException(e); }
 }
 public synchronized List<Document> list() {
  try (var files = Files.list(root.resolve("documents"))) {
   return files.filter(p -> p.toString().endsWith(".json")).map(p -> {
    try { return decode(Files.readString(p)); } catch (IOException e) { throw new IllegalStateException(e); }
   }).sorted(Comparator.comparing(Document::creadoEn).reversed()).toList();
  } catch (IOException e) { throw new IllegalStateException(e); }
 }
 public synchronized boolean replace(Document previous, Document next) {
  var current = find(previous.documentId());
  if (current.isEmpty() || !current.get().equals(previous)) return false;
  atomic(record(next.documentId()), encode(next).getBytes(java.nio.charset.StandardCharsets.UTF_8)); return true;
 }
 public void putFile(String id, String ext, byte[] data) {
  checkId(id); checkExtension(ext); atomic(root.resolve("files").resolve(id + "." + ext), data);
 }
 public byte[] getFile(String id, String ext) {
  checkId(id); checkExtension(ext);
  try { return Files.readAllBytes(root.resolve("files").resolve(id + "." + ext)); }
  catch (NoSuchFileException e) { throw new ApiException(404,"Archivo no encontrado"); }
  catch (IOException e) { throw new IllegalStateException(e); }
 }
}