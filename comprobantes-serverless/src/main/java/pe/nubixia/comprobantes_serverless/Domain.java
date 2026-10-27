package pe.nubixia.comprobantes_serverless;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.math.*;
import java.time.*;
import java.util.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public final class Domain {
 private Domain() {}
 public static final ObjectMapper JSON = new ObjectMapper().registerModule(new JavaTimeModule());
 public record Item(String descripcion, BigDecimal cantidad, BigDecimal precioUnitario) {}
 public record Invoice(String rucEmisor, String cliente, String fecha, String serie, String numero,
                       List<Item> items, BigDecimal subtotal, BigDecimal igv, BigDecimal total) {}
 public record Event(String estado, String fecha, String detalle) {}
 public record Document(String documentId, String fingerprint, Invoice comprobante, String estado,
   String creadoEn, String actualizadoEn, List<Event> historial, String error, long leaseUntil) {
   Document transition(String state, String detail, long lease) {
    String now = Instant.now().toString();
    var history = new ArrayList<>(historial); history.add(new Event(state, now, detail));
    return new Document(documentId, fingerprint, comprobante, state, creadoEn, now, history,
      state.equals("ERROR") || state.equals("RECHAZADO") ? detail : null, lease);
   }
 }
 public static class ApiException extends RuntimeException {
  public final int status;
  public ApiException(int status, String message) { super(message); this.status = status; }
 }
 static BigDecimal money(BigDecimal n) { return n.setScale(2, RoundingMode.HALF_UP); }
 static void require(boolean valid, String message) { if (!valid) throw new ApiException(400, message); }
 public static Invoice validate(Invoice i) {
  require(i != null, "El cuerpo JSON es obligatorio");
  require(i.rucEmisor != null && i.rucEmisor.matches("[0-9]{11}"), "rucEmisor debe tener 11 dígitos");
  require(i.cliente != null && !i.cliente.isBlank() && i.cliente.length() <= 200, "cliente es obligatorio (máximo 200 caracteres)");
  try { LocalDate.parse(i.fecha); } catch (Exception e) { throw new ApiException(400, "fecha debe ser una fecha válida YYYY-MM-DD"); }
  require(i.serie != null && i.serie.matches("[FB][A-Z0-9]{3}"), "serie debe tener formato F001 o B001");
  require(i.numero != null && i.numero.matches("[0-9]{1,8}") && Long.parseLong(i.numero) > 0, "numero debe tener entre 1 y 8 dígitos y ser mayor que cero");
  require(i.items != null && !i.items.isEmpty() && i.items.size() <= 100, "items debe contener entre 1 y 100 productos");
  BigDecimal subtotal = BigDecimal.ZERO;
  for (Item item : i.items) {
   require(item != null && item.descripcion != null && !item.descripcion.isBlank() && item.descripcion.length() <= 200, "Cada ítem debe tener descripción (máximo 200 caracteres)");
   require(item.cantidad != null && item.cantidad.signum() > 0 && item.cantidad.compareTo(new BigDecimal("1000000")) <= 0 && item.cantidad.scale() <= 3, "cantidad debe ser positiva, con hasta 3 decimales y máximo 1000000");
   require(item.precioUnitario != null && item.precioUnitario.signum() >= 0 && item.precioUnitario.compareTo(new BigDecimal("10000000")) <= 0 && item.precioUnitario.scale() <= 2, "precioUnitario debe ser no negativo con hasta 2 decimales y máximo 10000000");
   subtotal = subtotal.add(money(item.cantidad.multiply(item.precioUnitario)));
  }
  BigDecimal igv = money(subtotal.multiply(new BigDecimal("0.18")));
  require(i.subtotal != null && i.igv != null && i.total != null, "subtotal, igv y total son obligatorios");
  require(i.subtotal.compareTo(subtotal) == 0 && i.igv.compareTo(igv) == 0 && i.total.compareTo(subtotal.add(igv)) == 0, "Importes inconsistentes: subtotal=" + subtotal + ", igv=" + igv + ", total=" + subtotal.add(igv));
  return new Invoice(i.rucEmisor, i.cliente.strip(), i.fecha, i.serie, Long.toString(Long.parseLong(i.numero)), List.copyOf(i.items), money(subtotal), igv, money(subtotal.add(igv)));
 }
 static String hash(String value) {
  try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8))); }
  catch (Exception e) { throw new IllegalStateException(e); }
 }
 static String encode(Object value) { try { return JSON.writeValueAsString(value); } catch (Exception e) { throw new IllegalStateException(e); } }
 static Document decode(String value) { try { return JSON.readValue(value, Document.class); } catch (Exception e) { throw new IllegalStateException(e); } }
}