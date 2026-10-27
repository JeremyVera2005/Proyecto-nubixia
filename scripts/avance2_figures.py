from pathlib import Path
import html
root=Path.cwd();out=root/'.tools/avance2_sources/figures';out.mkdir(exist_ok=True)
def text(x,y,lines,size=34,anchor='middle',weight='normal'):
 return ''.join(f'<text x="{x}" y="{y+i*(size+8)}" font-family="Arial" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="#17212b">{html.escape(t)}</text>' for i,t in enumerate(lines))
def box(x,y,w,h,title,lines):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#f5f7f9" stroke="#435366" stroke-width="3"/>'+text(x+w/2,y+48,[title],40,weight='bold')+text(x+w/2,y+91,lines,32)
def arrow(path,label='',x=0,y=0,dash=False):
 return f'<path d="{path}" fill="none" stroke="#34495e" stroke-width="4" marker-end="url(#arrow)"'+(' stroke-dasharray="12 8"' if dash else '')+'/>'+ (text(x,y,[label],29) if label else '')
header='<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1430" viewBox="0 0 1800 1430"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#34495e"/></marker></defs><rect width="1800" height="1430" fill="white"/>'
s=header
s+=f'<rect x="40" y="205" width="1720" height="1150" rx="14" fill="white" stroke="#7d8996" stroke-width="3" stroke-dasharray="15 10"/>'
s+=text(75,191,['AWS us east 2  Servicios administrados  Sin VPC propia'],30,anchor='start')
s+=box(650,22,500,130,'Usuario PYME',['Navegador Angular'])
s+=box(650,260,500,135,'API Gateway REST',['HTTPS y authorizer JWT'])
s+=box(1260,260,430,135,'Amazon Cognito',['Registro y acceso'])
s+=arrow('M900 152 V260','HTTPS',1020,220)
s+=arrow('M1150 325 H1260','JWT',1200,300)
s+=box(650,485,500,135,'Lambda API',['Java 17  Web y datos'])
s+=arrow('M900 395 V485','Invocación',1050,453)
s+=box(85,705,470,135,'DynamoDB',['owner estado e historial'])
s+=arrow('M650 552 H320 V705','Registro y consulta',330,525)
s+=box(85,965,470,100,'Stream INSERT',[])
s+=arrow('M320 840 V965','Evento durable',475,917)
s+=box(650,965,500,100,'Lambda publicadora',[])
s+=arrow('M555 1015 H650')
s+=box(1260,965,430,100,'Amazon SQS y DLQ',[])
s+=arrow('M1150 1015 H1260')
s+=box(1260,1175,430,135,'Lambda procesadora',['Genera XML y PDF'])
s+=arrow('M1475 1065 V1175','Lotes y reintentos',1465,1130)
s+=box(650,1175,500,135,'Amazon S3 privado',['Archivos por documentId'])
s+=arrow('M1260 1240 H1150','PUT',1200,1208)
s+=arrow('M1690 1235 H1730 V655 H320 V705','Actualiza estados',1350,646)
s+=box(85,1175,470,135,'CloudWatch e IAM',['Logs y permisos acotados'])
s+=arrow('M650 555 H65 V1245 H85','Logs',124,569,True)
s+=arrow('M1150 85 H1785 V1395 H900 V1310','GET con URL firmada',1080,1386,True)
s+='</svg>'
(out/'arquitectura_actual.svg').write_text(s,encoding='utf-8')
s='<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="860" viewBox="0 0 1800 860"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#34495e"/></marker></defs><rect width="1800" height="860" fill="white"/>'
s+=text(900,50,['Límites de acceso y confianza del MVP'],42,weight='bold')
s+='<rect x="30" y="100" width="740" height="500" rx="12" fill="#f5f7f9" stroke="#69788a" stroke-width="3"/>'
s+=text(400,152,['Acceso público por HTTPS'],35,weight='bold')
s+=box(95,200,610,130,'Sitio y Cognito',['Contenido público y credenciales'])
s+=box(95,410,610,130,'API de comprobantes',['JWT válido antes de ejecutar datos'])
s+='<rect x="970" y="100" width="800" height="500" rx="12" fill="white" stroke="#69788a" stroke-width="3"/>'
s+=text(1370,152,['Autorización de recursos'],35,weight='bold')
s+=box(1060,200,620,130,'DynamoDB y SQS',['Permisos IAM de las Lambda'])
s+=box(1060,410,620,130,'S3 sin acceso anónimo',['Firma temporal y cifrado SSE S3'])
s+=arrow('M705 475 H1060','IAM',882,449)
s+=arrow('M705 270 H840 V675 H1370 V540','Descarga solo con URL firmada',1090,718,True)
s+=text(900,800,['Privado por autorización no significa desplegado en una subred privada'],32)
s+='</svg>'
(out/'red_y_accesos.svg').write_text(s,encoding='utf-8')
print(out)
