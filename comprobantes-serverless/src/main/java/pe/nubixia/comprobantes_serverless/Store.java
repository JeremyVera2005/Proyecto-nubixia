package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.util.*;
public interface Store {
 default String namespace() { return ""; }
 boolean create(Document document);
 Optional<Document> find(String id);
 List<Document> list();
 boolean replace(Document previous, Document next);
 void putFile(String id, String extension, byte[] data);
 byte[] getFile(String id, String extension);
 default String downloadUrl(String id, String extension) { return null; }
}
