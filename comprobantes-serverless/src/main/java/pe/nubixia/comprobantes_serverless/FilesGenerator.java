package pe.nubixia.comprobantes_serverless;
import static pe.nubixia.comprobantes_serverless.Domain.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import javax.xml.stream.*;
import org.apache.pdfbox.pdmodel.*;
import org.apache.pdfbox.pdmodel.font.*;
import org.apache.pdfbox.pdmodel.common.PDRectangle;

public final class FilesGenerator {
 public byte[] xml(Document d) throws Exception {
  var buffer = new ByteArrayOutputStream();
  var w = XMLOutputFactory.newFactory().createXMLStreamWriter(buffer,"UTF-8");
  w.writeStartDocument("UTF-8","1.0"); w.writeStartElement("ComprobanteAcademico");
  w.writeAttribute("sinValidezTributaria","true");
  element(w,"DocumentId",d.documentId()); var i=d.comprobante();
  element(w,"RucEmisor",i.rucEmisor()); element(w,"Cliente",i.cliente()); element(w,"Fecha",i.fecha());
  element(w,"Serie",i.serie()); element(w,"Numero",i.numero()); element(w,"Moneda","PEN");
  w.writeStartElement("Items");
  for(var item:i.items()) { w.writeStartElement("Item");
   element(w,"Descripcion",item.descripcion()); element(w,"Cantidad",item.cantidad().toPlainString());
   element(w,"PrecioUnitario",item.precioUnitario().toPlainString());
   element(w,"Importe",money(item.cantidad().multiply(item.precioUnitario())).toPlainString()); w.writeEndElement();
  }
  w.writeEndElement(); element(w,"Subtotal",i.subtotal().toPlainString()); element(w,"IGV",i.igv().toPlainString());
  element(w,"Total",i.total().toPlainString()); w.writeEndElement(); w.writeEndDocument(); w.close(); return buffer.toByteArray();
 }
 private void element(XMLStreamWriter w,String key,String text) throws Exception { w.writeStartElement(key); w.writeCharacters(text); w.writeEndElement(); }
 public byte[] pdf(Document d) throws Exception {
  try(var pdf=new PDDocument(); var out=new ByteArrayOutputStream()) {
   var i=d.comprobante(); var lines=new ArrayList<String>();
   lines.add("NUBIXIA | Comprobante academico"); lines.add("SIMULACION - SIN VALIDEZ TRIBUTARIA");
   lines.add(i.serie()+"-"+i.numero()+" | Fecha: "+i.fecha()); lines.add("RUC emisor: "+i.rucEmisor());
   wrap(lines,"Cliente: "+i.cliente()); lines.add("ID: "+d.documentId()); lines.add(" ");
   lines.add("Descripcion | Cantidad x Precio unitario = Importe (S/)"); lines.add(" ");
   for(var item:i.items()) { wrap(lines,item.descripcion()); lines.add("  "+item.cantidad().toPlainString()+" x "+item.precioUnitario().toPlainString()+" = "+money(item.cantidad().multiply(item.precioUnitario()))); }
   lines.add(" "); lines.add("Subtotal: S/ "+i.subtotal()); lines.add("IGV (18%): S/ "+i.igv()); lines.add("TOTAL: S/ "+i.total());
   var font=new PDType1Font(Standard14Fonts.FontName.HELVETICA);
   for(int offset=0;offset<lines.size();offset+=46) {
    var page=new PDPage(PDRectangle.A4); pdf.addPage(page);
    try(var stream=new PDPageContentStream(pdf,page)) {
     stream.beginText(); stream.setFont(font,10); stream.setLeading(16); stream.newLineAtOffset(40,790);
     for(String line:lines.subList(offset,Math.min(offset+46,lines.size()))) {
      // Standard PDF fonts have limited glyphs; replace unsupported characters predictably.
      StringBuilder safe=new StringBuilder();
      for(int cp:line.codePoints().toArray()) {
       String c=new String(Character.toChars(cp));
       try { font.encode(c); safe.append(c); } catch(IllegalArgumentException e) { safe.append("?"); }
      }
      stream.showText(safe.toString()); stream.newLine();
     }
     stream.endText();
    }
   }
   pdf.save(out); return out.toByteArray();
  }
 }
 private void wrap(List<String> lines,String value) {
  String clean=value.replaceAll("[\\p{Cntrl}]"," ");
  while(clean.length()>85) { lines.add(clean.substring(0,85)); clean=clean.substring(85); } lines.add(clean);
 }
}