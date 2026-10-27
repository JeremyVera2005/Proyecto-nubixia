import java.nio.file.*;
import java.io.*;
import java.util.*;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.nodes.*;

class ValidateTemplate {
 static Node field(MappingNode map,String key) {
  for(var pair:map.getValue()) if(((ScalarNode)pair.getKeyNode()).getValue().equals(key)) return pair.getValueNode();
  throw new IllegalStateException("Falta propiedad: "+key);
 }
 static String text(Node n) { return ((ScalarNode)n).getValue(); }
 public static void main(String[] args) throws Exception {
  Path path=Path.of(args[0]).toAbsolutePath();
  MappingNode root;
  try(var r=Files.newBufferedReader(path)) { root=(MappingNode)new Yaml().compose(r); }
  MappingNode resources=(MappingNode)field(root,"Resources");
  var types=new HashSet<String>();
  for(var resource:resources.getValue()) types.add(text(field((MappingNode)resource.getValueNode(),"Type")));
  for(String type:List.of("AWS::Serverless::Api","AWS::Serverless::Function","AWS::DynamoDB::Table","AWS::SQS::Queue","AWS::S3::Bucket","AWS::Logs::LogGroup"))
   if(!types.contains(type)) throw new IllegalStateException("Falta servicio: "+type);
  MappingNode globals=(MappingNode)field((MappingNode)field(root,"Globals"),"Function");
  Path jar=path.getParent().resolve(text(field(globals,"CodeUri"))).normalize();
  if(!Files.isRegularFile(jar)) throw new IllegalStateException("No existe el JAR: "+jar);
  System.out.println("YAML correcto. Servicios requeridos presentes. Artefacto Lambda encontrado.");
  System.out.println("Esta comprobación local no sustituye sam validate --lint ni un despliegue real.");
 }
}
