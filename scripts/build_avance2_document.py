from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib, json
from lxml import etree
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_SECTION_START
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'.tools/avance2_sources'
REF=TMP/'reference.docx'
OUT=ROOT/'docs/entregables/Avance_Proyecto_1_y_2_Nubixia.docx'
OUT.parent.mkdir(parents=True,exist_ok=True)
doc=Document(REF)
canon=lambda e: etree.tostring(e,method='c14n')
original=[canon(e) for e in list(doc._element.body)[:-1]]
for name,size,bold in [('A2Body',11,False),('A2H1',13,True),('A2H2',12,True),('A2Small',9.5,False)]:
    s=doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
    s.font.name='Arial'; s.font.size=Pt(size); s.font.bold=bold; s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(7)
    s.paragraph_format.line_spacing=1.08
    if bold:s.paragraph_format.keep_with_next=True
sec=doc.add_section(WD_SECTION_START.NEW_PAGE)
sec.header.is_linked_to_previous=False; sec.footer.is_linked_to_previous=False
hp=sec.header.paragraphs[0]; hp.style='A2Small'; hp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
hp.add_run('NUBIXIA  |  SERVICIOS CLOUD  |  ÁREA 5 TEMA 10')
fp=sec.footer.paragraphs[0]; fp.style='A2Small'; fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
fp.add_run('Página ')
def field(p,code,value='0'):
    if code.startswith('PAGEREF a2_'):
        index=int(code.split()[1].split('_')[1]);value=str(index+9+(2 if index>=13 else 0))
    elif code=='PAGE':value='9'
    elif code=='NUMPAGES':value='26'
    r=p.add_run(); a=OxmlElement('w:fldChar');a.set(qn('w:fldCharType'),'begin');r._r.append(a)
    r=p.add_run();a=OxmlElement('w:instrText');a.set(qn('xml:space'),'preserve');a.text=' '+code+' ';r._r.append(a)
    r=p.add_run();a=OxmlElement('w:fldChar');a.set(qn('w:fldCharType'),'separate');r._r.append(a)
    p.add_run(value)
    r=p.add_run();a=OxmlElement('w:fldChar');a.set(qn('w:fldCharType'),'end');r._r.append(a)
field(fp,'PAGE');fp.add_run(' de ');field(fp,'NUMPAGES')
def p(text,small=False):
    return doc.add_paragraph(text,'A2Small' if small else 'A2Body')
heads=[]
def h(title,new=True):
    e=doc.add_paragraph(title,'A2H1');e.paragraph_format.page_break_before=new
    name='a2_'+str(len(heads)+1);heads.append((name,title))
    a=OxmlElement('w:bookmarkStart');a.set(qn('w:id'),str(500+len(heads)));a.set(qn('w:name'),name)
    e._p.insert(0,a);a=OxmlElement('w:bookmarkEnd');a.set(qn('w:id'),str(500+len(heads)));e._p.append(a)
    return e
def sub(t):return doc.add_paragraph(t,'A2H2')
def table(headers,rows,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Inches(w)
    for c,x,w in zip(t.rows[0].cells,headers,widths):c.width=Inches(w);c.text=x
    for row in rows:
        cells=t.add_row().cells
        for c,x,w in zip(cells,row,widths):c.width=Inches(w);c.text=str(x)
    pr=t._tbl.tblPr
    b=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');b.append(el)
    pr.append(b)
    margins=OxmlElement('w:tblCellMar')
    for side in ['top','left','bottom','right']:
        el=OxmlElement('w:'+side);el.set(qn('w:w'),'85');el.set(qn('w:type'),'dxa');margins.append(el)
    pr.append(margins)
    for i,row in enumerate(t.rows):
        rp=row._tr.get_or_add_trPr();rp.append(OxmlElement('w:cantSplit'))
        if i==0:rp.append(OxmlElement('w:tblHeader'))
        for j,c in enumerate(row.cells):
            if i==0:
                el=OxmlElement('w:shd');el.set(qn('w:fill'),'EAEAEA');c._tc.get_or_add_tcPr().append(el)
            for para in c.paragraphs:
                para.style='A2Small';para.paragraph_format.space_after=Pt(2);para.paragraph_format.space_before=Pt(2)
                for r in para.runs:r.font.size=Pt(10);r.bold=i==0
    p('',True)
    return t
def image(path,caption,width=5.85):
    para=doc.add_paragraph();para.paragraph_format.keep_with_next=True
    pic=para.add_run().add_picture(str(path),width=Inches(width))
    pic._inline.docPr.set('descr',caption)
    p(caption,True)

if 'Title' not in doc.styles:doc.styles.add_style('Title',WD_STYLE_TYPE.PARAGRAPH)
title=doc.add_paragraph('AVANCE 2 DE INFRAESTRUCTURA BASE','Title')
for r in title.runs:r.font.name='Arial';r.font.size=Pt(16);r.font.color.rgb=RGBColor(0,0,0)
p('Semana 12  |  Hito del 40 por ciento  |  Continuación del Avance 1')
p('Área 5  •  Tema 10  •  Sistema de facturación electrónica serverless Nubixia')
p('Ashton Patrick Jeremy Vera Jara  |  U22217157\nServicios Cloud 45099\nDocente Hernandez Naveda Ramiro Jose\nCorte documental 26 de octubre de 2026')
p('Esta segunda parte continúa la propuesta original conservada en las páginas anteriores. Describe la implementación comprobable, su infraestructura en AWS, las pruebas disponibles y las brechas frente a la rúbrica de la semana 12. El 40 por ciento identifica el hito académico solicitado; no representa una calificación ni una medición automática del cumplimiento.')
p('La solución procesa comprobantes ficticios con servicios administrados y dispone de una web con autenticación. La red VPC con máquinas virtuales, Docker, el historial Git y Step Functions todavía requieren trabajo o una adecuación de la rúbrica aprobada por el docente. No se presentan como implementados.')
sub('Índice de la continuación')
titles=['Continuidad del proyecto y alcance','Correspondencia con la rúbrica de la semana 12','Arquitectura cloud implementada','Topología lógica y conectividad','Aprovisionamiento de cómputo y almacenamiento','Modelo de datos y contratos de la API','Empaquetamiento e infraestructura como código','Seguridad e identidad','Pruebas y resultados verificables','Dimensionamiento y estimación de costos','Continuidad operativa y riesgos','Plan actualizado y sustentación','Evidencias del sitio publicado','Evidencias del procesamiento y trazabilidad','Conclusiones y referencias']
for i,t in enumerate(titles,1):
    z=p(f'{i}. {t}  ·  ',True);field(z,f'PAGEREF a2_{i} \\h')

h('1 CONTINUIDAD DEL PROYECTO Y ALCANCE')
p('El Avance 1 planteó un MVP académico para recibir comprobantes, validar su contenido, procesarlos por eventos y consultar el resultado. Esta continuación mantiene el mismo problema y la misma separación entre recepción y procesamiento. La base implementada utiliza API Gateway, Lambda, SQS, DynamoDB, S3 y CloudWatch.')
table(['Propuesta inicial','Estado implementado o pendiente'],[
('Dos funciones Lambda','Se separaron tres responsabilidades: API, publicación desde DynamoDB Streams y procesamiento de SQS.'),
('API con API key o JWT','Las operaciones de comprobantes exigen JWT de Cognito y separan los datos por usuario.'),
('Portal avanzado fuera del MVP','Se amplió el alcance por solicitud posterior: landing, ingreso, registro y recuperación de contraseña.'),
('XML y PDF almacenados en S3','Se generan documentos ficticios. La descarga usa enlaces firmados de corta vigencia.'),
('Concurrencia de 20 solicitudes','Las ráfagas de 20 todavía presentan errores. La prueba con concurrencia de dos logró 20 recepciones.'),
('Integración tributaria productiva excluida','Se conserva la exclusión de SUNAT/OSE, certificados y firma legal. Debe ratificarse con el docente frente al catálogo del tema.')],[2.05,3.85])
p('La fecha y la planificación del primer avance permanecen como registro de la propuesta. Las diferencias expuestas aquí representan la evolución del proyecto y no sustituyen retrospectivamente sus compromisos. La planificación se interpreta por hitos académicos; no se atribuyen fechas reales de ejecución que no estén documentadas.')
sub('Objetivo de esta entrega')
p('Sustentar la infraestructura serverless disponible, explicar cómo se conectan el frontend, la API y la persistencia, y demostrar el procesamiento con evidencia reproducible. La entrega también identifica las actividades necesarias para completar los criterios literales del APF2 y la orquestación del tema seleccionado.')

h('2 CORRESPONDENCIA CON LA RÚBRICA DE LA SEMANA 12')
p('La rúbrica APF2 se denomina Infraestructura base, redes y contenerización. Sus cuatro criterios suman 20 puntos [1]. La siguiente matriz contrasta sus exigencias con la evidencia disponible; la evaluación corresponde al docente.')
table(['Criterio y peso','Evidencia disponible','Brecha literal'],[
('Red virtual 4 puntos','Diagrama lógico, HTTPS, IAM y servicios administrados.','No hay VPC propia, subredes públicas y privadas, rutas, NAT/IGW ni grupos de seguridad configurados.'),
('Cómputo y almacenamiento 4 puntos','Tres Lambda, DynamoDB, S3 y SQS desplegados mediante CloudFormation.','No existen VM ni conexión de esas VM a una red privada.'),
('Docker 4 puntos','JAR Java y compilación Angular empaquetados para Lambda.','No se dispone de Dockerfiles multietapa ni ejecución multicontenedor verificada.'),
('Git documentación y defensa 8 puntos','Código, manifiesto, scripts, pruebas y este informe.','La carpeta revisada no es un repositorio Git; faltan commits trazables y URL de entrega.')],[1.25,2.25,2.4])
sub('Adecuación al enfoque serverless')
p('El uso de servicios administrados evita operar servidores y gateways con cargo fijo para una demostración escolar. Esa decisión explica la arquitectura, pero no equivale por sí sola al cumplimiento de VPC, VM o Docker. Se debe solicitar al docente la aceptación explícita de una equivalencia serverless o implementar los requisitos que indique, con revisión previa del costo.')
p('El catálogo ubica la facturación serverless en el área 5, tema 10, e incluye una máquina de estados con Step Functions o Logic Apps [2]. La implementación actual usa coreografía por eventos y no contiene Step Functions. Por tanto, la orquestación explícita permanece pendiente. El alcance ficticio también requiere ratificación si la evaluación exige firma y envío tributario reales.')

h('3 ARQUITECTURA CLOUD IMPLEMENTADA')
p('La infraestructura principal se encuentra en us-east-2, región Ohio, en la pila nubixia-escolar-demo. El mismo punto de entrada publica la aplicación Angular y atiende la API. El almacenamiento de comprobantes se mantiene separado de los recursos estáticos empaquetados dentro del backend.')
image(TMP/'figures/arquitectura_actual.png','Figura A2 1. Componentes y flujo implementados. Elaboración propia a partir del código y la plantilla CloudFormation.')
p('El navegador obtiene su configuración pública, se autentica en Cognito y envía el ID token a API Gateway. La función de API valida el comprobante y lo registra en DynamoDB. El evento INSERT del stream activa Publisher, que entrega el identificador a SQS. Processor consume la cola, genera XML y PDF, guarda ambos en S3 y actualiza el estado. La interfaz consulta el resultado mediante la API.')
p('Las tres funciones cumplen responsabilidades distintas. Publisher desacopla la escritura de la entrega a la cola. Processor admite reintentos y DLQ. La API controla la propiedad de los datos antes de consultar o emitir una URL firmada. CloudWatch recibe registros de ejecución; no se ha implementado una máquina de estados.')

h('4 TOPOLOGÍA LÓGICA Y CONECTIVIDAD')
p('Las funciones no tienen VpcConfig en la plantilla. Usan la conectividad administrada de Lambda y los endpoints de los servicios AWS. No se desplegaron subredes propias, NAT Gateway, máquinas EC2 ni una base de datos dentro de una subred privada. La documentación de Lambda diferencia este funcionamiento de la conexión explícita a una VPC del cliente [4].')
image(TMP/'figures/red_y_accesos.png','Figura A2 2. Límites de acceso y conectividad lógica. Un recurso privado por autorización no equivale a un recurso dentro de una subred privada.')
table(['Origen y destino','Canal y control'],[
('Navegador a web y API','HTTPS. Los endpoints de negocio requieren JWT; los archivos de la web son públicos.'),
('Navegador a Cognito','HTTPS con cliente público sin secreto para registro y autenticación.'),
('Lambda a DynamoDB SQS y S3','API de servicio y permisos IAM del rol de ejecución.'),
('Navegador a S3','HTTPS mediante URL firmada por cinco minutos, emitida después de validar propietario y estado.')],[2.15,3.75])
p('El bloqueo de acceso público de S3 y la autorización de DynamoDB protegen los datos por políticas. La API sigue siendo un endpoint público autenticado. Esta distinción debe explicarse durante la sustentación y no presentarse como evidencia de segmentación de una VPC.')

h('5 APROVISIONAMIENTO DE CÓMPUTO Y ALMACENAMIENTO')
table(['Recurso','Configuración documentada'],[
('Lambda','Java 17, tres funciones, 512 MB y timeout de 30 segundos. API 2.0.1; Publisher y Processor 2.0.0.'),
('DynamoDB','PAY_PER_REQUEST, clave documentId de tipo String, propietario y payload; stream NEW_IMAGE.'),
('SQS principal','Cola Standard, visibilidad 180 segundos, retención de cuatro días, lote de cinco y concurrencia máxima dos.'),
('Cola de errores','Redrive después de cinco recepciones; retención de catorce días.'),
('S3','Bucket privado, bloqueo público completo, cifrado SSE-S3 y denegación de tráfico HTTP.'),
('API Gateway','API REST, etapa demo y authorizer Cognito para rutas de negocio.'),
('Cognito','Pool Lite, cliente público sin secreto, ID token de quince minutos y refresh token de un día.'),
('CloudWatch','Tres grupos de registros con retención de tres días. Sin panel ni alarmas específicas desplegadas.')],[1.4,4.5])
p('CloudFormation declara los recursos y sus relaciones, mientras los scripts compilan y publican los artefactos. La persistencia en AWS utiliza DynamoDB y S3. H2 y Flyway pertenecen únicamente a la ejecución local; no constituyen la base de datos desplegada en AWS.')
p('La publicación mediante una distribución CloudFront propia se intentó, pero AWS devolvió una restricción de verificación de cuenta. Por ello no se presenta CloudFront como recurso propio activo. El pool Cognito retenido de ese intento se reutiliza; el cliente se administra desde la pila principal. Esta dependencia deberá ordenarse antes de una migración o eliminación de recursos.')
p('No están configurados PITR, copias periódicas ni recuperación multirregión. La retención de una cola o de los logs no sustituye un respaldo de la base de datos. El dimensionamiento actual es de demostración y no acredita disponibilidad productiva.')

h('6 MODELO DE DATOS Y CONTRATOS DE LA API')
p('DynamoDB conserva el estado y la información del comprobante. S3 almacena sus archivos derivados. El identificador incorpora el usuario y los datos del documento, de manera que dos usuarios no compartan accidentalmente el mismo espacio de idempotencia.')
table(['Campo o concepto','Uso'],[
('documentId','Clave del documento, derivada de propietario, RUC, serie y número.'),
('owner','Identificador sub del usuario autenticado; se obtiene del contexto confiable del authorizer.'),
('payload','Contenido de negocio serializado como JSON: emisor, cliente, fecha e ítems.'),
('Estado y control','Estado de procesamiento, huella del contenido y mecanismos de exclusión o actualización condicional.')],[1.5,4.4])
table(['Operación','Contrato funcional'],[
('Crear comprobante','POST: valida el cuerpo, registra de forma condicional y devuelve recepción 202.'),
('Listar comprobantes','GET: devuelve documentos visibles para el propietario autenticado.'),
('Consultar detalle','GET por identificador: exige propiedad del documento.'),
('Descargar XML o PDF','GET de archivo: emite URL firmada si pertenece al usuario y está ACEPTADO.'),
('Corregir y reenviar','Actualización controlada del documento según estado y huella del contenido.')],[1.65,4.25])
p('Los cálculos monetarios utilizan BigDecimal y redondeo explícito para subtotal, IGV del 18 por ciento y total. La recepción distingue contenido inválido y conflictos de idempotencia. La escritura condicional evita reemplazos silenciosos y la actualización usa comparación del estado o versión esperada.')
p('La entrega Standard de SQS puede repetirse. El procesador usa una concesión temporal de 90 segundos y controles de estado para reducir duplicados; esto no constituye una garantía de entrega exactamente una vez. La lista actual usa Scan filtrado por owner: el filtro protege la salida, pero no reduce las lecturas consumidas. Un índice y Query por propietario son mejoras necesarias al crecer.')

h('7 EMPAQUETAMIENTO E INFRAESTRUCTURA COMO CÓDIGO')
p('El frontend utiliza Angular 22 y TypeScript 6. El backend se desarrolla con Java 17 y Spring Boot 3.5.7 para el entorno local; en AWS se ejecutan handlers Java de Lambda. La compilación Angular usa la base /demo/ y sus archivos se incorporan al paquete web servido por la función de API.')
table(['Ubicación','Contenido y propósito'],[
('comprobantes-serverless','Lógica Java, adaptadores de persistencia, handlers y pruebas.'),
('Frontend Angular','Vistas, autenticación, llamadas a la API y recursos visuales.'),
('infra','Plantilla CloudFormation y políticas de despliegue.'),
('scripts','Compilación, preparación de artefactos, despliegue y verificación.'),
('docs y evidencias','Guías de operación, contratos y resultados JSON o capturas.')],[1.65,4.25])
sub('Procedimiento de actualización')
p('1. Modificar el componente o estilo y comprobarlo localmente. 2. Compilar el frontend con la base de la etapa demo. 3. Incorporar el resultado al paquete de la API y generar el JAR. 4. Publicar una nueva versión del artefacto y actualizar la función o la pila con los scripts del proyecto. 5. Verificar web, autenticación, recepción y consulta después del cambio. Como la web está empaquetada en la API, un cambio de diseño también requiere actualizar ese artefacto.')
p('La configuración pública contiene región, endpoint y datos públicos del cliente Cognito; no contiene una API key secreta. Las credenciales de despliegue deben permanecer fuera del código y de la entrega académica. Los archivos locales de secretos, dependencias descargadas y paquetes temporales no deben publicarse.')
sub('Estado de Docker y Git')
p('El empaquetamiento actual produce archivos estáticos y JAR; no existen Dockerfiles ni una prueba multicontenedor. La inspección de la carpeta tampoco encontró un repositorio Git operativo. El ZIP de código facilita compartir la fuente, pero no acredita historial. Para cerrar el criterio se requiere inicializar un repositorio con identidad real, registrar cambios comprensibles, revisar secretos y adjuntar la URL o el repositorio solicitado por el docente. No se han fabricado commits ni publicado archivos a terceros para esta documentación.')

h('8 SEGURIDAD E IDENTIDAD')
p('Cognito administra registro, confirmación por correo, ingreso y recuperación de contraseña. API Gateway verifica el JWT antes de invocar las operaciones protegidas. El backend toma el sub del contexto del authorizer y vuelve a comprobar que el documento pertenece a ese usuario antes de devolver información o enlaces.')
table(['Elemento','Control implementado o limitación'],[
('Cliente web','Cliente Cognito público sin secreto. El usuario introduce sus credenciales en el flujo de la aplicación.'),
('API','JWT requerido en negocio; solicitudes sin token y con token inválido retornaron 401 en la verificación disponible.'),
('Aislamiento de datos','Propiedad por usuario. Los datos históricos sin owner no se muestran como documentos de nuevos usuarios.'),
('Archivos','S3 privado y URL firmada de cinco minutos para XML o PDF aceptados.'),
('Funciones','Roles IAM para acceder a servicios según la responsabilidad de cada función.'),
('Despliegue','Rol ampliado con autorización previa para Cognito y CloudFront. Revisar permisos residuales de CloudFront no utilizado.')],[1.35,4.55])
p('Se verificaron respuestas negativas reales de Cognito para credenciales inválidas y contraseña débil. No hay evidencia de una sesión positiva completa con un usuario recién confirmado después de incorporar Cognito. La entrega del correo y el recorrido registro, confirmación, ingreso y comprobante propio requieren validación adicional.')
p('La API key histórica no sustituye a JWT. La cuota de 500 solicitudes por día vinculada al uso de una API key no limita automáticamente las rutas actuales que solo exigen JWT. El throttle de una solicitud por segundo por método con ráfaga de 25 es un control de mejor esfuerzo, no un techo garantizado de gasto.')
p('No se acredita una auditoría completa de mínimo privilegio, pruebas de penetración, WAF ni MFA obligatorio. Los registros y capturas que se compartan con el docente deben omitir tokens, claves y datos personales reales. Los comprobantes de demostración permanecen ficticios y no tienen validez tributaria.')

h('9 PRUEBAS Y RESULTADOS VERIFICABLES')
p('La evidencia disponible incluye 21 pruebas Java y 12 pruebas del frontend en dos suites. La verificación pública registra diez comprobaciones de recursos, configuración, cabeceras y autenticación negativa. Además, durante esta revisión documental el endpoint público respondió HTTP 200. Una respuesta de la página no demuestra por sí sola el funcionamiento completo de un usuario autenticado.')
table(['Escenario histórico','Recepciones HTTP 202','Resultado observado'],[
('Veinte solicitudes con concurrencia dos','20 de 20','Recepción de 192 a 546 ms; procesamiento de 230 a 1032 ms.'),
('Ráfaga fría de veinte simultáneas','10 de 20','Las restantes devolvieron 500; recepción máxima de 7165 ms y procesamiento superior a 15 s.'),
('Ráfaga caliente de veinte simultáneas','13 de 20','Persistieron errores 500 en las demás solicitudes.')],[2.1,1.05,2.75])
p('Estas mediciones corresponden al flujo anterior basado en API key, conservado en los JSON de evidencias. No se extrapolan a la versión autenticada con Cognito. La prueba escolar también comprobó idempotencia, rechazo de cuerpo inválido con 400, acceso no autorizado con 403 en esa versión, conflicto 409 y generación de XML de 587 bytes y PDF de 1142 bytes.')
p('Los errores HTTP ocurridos antes de la aceptación no demuestran pérdida de mensajes ya entregados a SQS. Sí evidencian que el objetivo de veinte solicitudes simultáneas no está logrado. Se debe correlacionar cada intento con logs y métricas antes de atribuir la causa a límites, arranque frío o errores del handler.')
sub('Validaciones pendientes para el siguiente hito')
p('Confirmar un usuario de prueba propio; crear, consultar y descargar un comprobante con JWT válido; verificar que otro usuario no accede al documento; repetir las ráfagas con identificadores de correlación; ensayar reintentos, duplicados y DLQ; restaurar un respaldo; y guardar resultados fechados con la versión probada. No se asigna una disponibilidad porcentual ni un SLA que estas pruebas no hayan medido.')

h('10 DIMENSIONAMIENTO Y ESTIMACIÓN DE COSTOS')
p('Se presenta una estimación mensual ilustrativa para Ohio, expresada en USD y sin impuestos. No es una factura ni una exportación de AWS Pricing Calculator. Se calculan importes brutos antes de créditos y franquicias gratuitas, con tarifas públicas consultadas el 26 de octubre de 2026 [5–11]. La facturación real depende de la cuenta y del consumo.')
p('Supuesto escolar: 1000 comprobantes, 10 usuarios activos, 9000 llamadas REST incluyendo archivos web, 11000 invocaciones Lambda y 1950 GB segundo con 512 MB. Se estiman 263000 operaciones SQS; este valor incluye 259200 sondeos vacíos hipotéticos de dos consumidores cada veinte segundos, no una medición del proyecto.')
table(['Servicio','Supuesto y tarifa de referencia','USD mes'],[
('API Gateway','9000 REST a 3,50 por millón','0,0315'),
('Lambda','11000 a 0,20 por millón y 1950 GB s a 0,0000166667','0,0347'),
('SQS','263000 operaciones Standard a 0,40 por millón','0,1052'),
('DynamoDB','2,01 M RRU a 0,125/M; 12000 WRU a 0,625/M; 0,01 GB a 0,25','0,2613'),
('S3','0,30 GB a 0,023; 2000 PUT a 0,005/1000 y 2000 GET a 0,0004/1000','0,0177'),
('CloudWatch','0,05 GB ingresados a 0,50; 0,005 GB retenidos a 0,03','0,0252'),
('Salida a Internet','0,50 GB a 0,09 como referencia','0,0450'),
('Cognito Lite','10 MAU a 0,0055 antes de franquicia aplicable','0,0550'),
('Total bruto aproximado','Suma con importes sin redondear','0,6755'),
('Margen del 10 por ciento','Total con margen aproximado de 0,74 USD','0,7431')],[1.2,3.8,0.9])
p('Las lecturas incluyen cuatro mil Scan de quinientos elementos de hasta 4 KB con lectura fuerte, más un margen. El listado puede dominar el consumo de DynamoDB. El tamaño de los ítems, la consistencia y el patrón de acceso deben medirse para reemplazar estos supuestos.')
p('Las franquicias aplicables podrían reducir el total; no se garantiza gratuidad. VM, NAT y RDS se excluyen porque no están desplegados. Almacenamiento y sondeos pueden consumir recursos sin actividad del usuario. Se recomienda revisar Billing, presupuestos y alertas; estas últimas no detienen automáticamente el gasto.')

h('11 CONTINUIDAD OPERATIVA Y RIESGOS')
p('La persistencia y los reintentos aportan tolerancia a fallos de ejecución, pero no constituyen un plan de recuperación completo. Los siguientes valores son objetivos propuestos para una demostración escolar y todavía no se han validado mediante un ensayo de restauración.')
table(['Objetivo propuesto','Acción pendiente y prueba'],[
('RPO de veinticuatro horas','Definir respaldo diario de datos y verificar qué información se perdería ante una restauración.'),
('RTO de sesenta minutos','Reconstruir la pila, restaurar datos, recuperar configuración y ejecutar una comprobación completa cronometrada.'),
('Reprocesamiento controlado','Inspeccionar DLQ, corregir causa y reinyectar mensajes sin duplicar archivos ni cambiar de propietario.')],[1.65,4.25])
table(['Riesgo','Tratamiento prioritario'],[
('Desalineación con APF2','Acordar por escrito la adecuación serverless o completar VPC, VM y Docker solicitados.'),
('Orquestación incompleta del tema','Diseñar Step Functions con estados, reintentos, errores y evidencia de ejecución.'),
('Errores en ráfagas','Instrumentar y repetir cargas; revisar límites y optimizar el recorrido antes de ampliar concurrencia.'),
('Pérdida o borrado de datos','Configurar y ensayar respaldos. La retención de tres días de logs limita el diagnóstico tardío.'),
('Consumo o permisos innecesarios','Optimizar Scan, revisar sondeos, recursos retenidos y permisos de despliegue no utilizados.')],[1.65,4.25])
p('El procedimiento operativo propuesto comienza por identificar el requestId y documentId, revisar el log de la función afectada y consultar el estado persistido. Si existe un mensaje en DLQ, debe resolverse su causa antes del reenvío. Un cambio de infraestructura debe conservar las dependencias de Cognito y los datos; eliminar una pila sin revisar políticas de retención puede interrumpir el acceso o destruir recursos.')

h('12 PLAN ACTUALIZADO Y SUSTENTACIÓN')
p('El WBS del primer avance se conserva como línea base. Este plan concreta las siguientes acciones por hito y distingue el trabajo disponible de lo que falta validar. No pretende reconstruir una cronología diaria sin evidencia.')
table(['Hito','Entregable y condición de cierre'],[
('Semana 12 APF2','Informe integrado, arquitectura, inventario, pruebas y matriz de brechas. Resolver adecuación de red y Docker con el docente.'),
('Después de APF2','Repositorio Git real, commits trazables, configuración sin secretos y procedimiento de compilación reproducible.'),
('Antes de APF3','Máquina de estados, reintentos, manejo de errores y pruebas de integración autenticadas.'),
('Semana 17 APF3 70 por ciento','Escalabilidad, métricas, alarmas y evidencia de resolución de la concurrencia objetivo.'),
('Cierre técnico','Respaldo y restauración ensayados, revisión de costos y permisos y manual de operación.'),
('Entrega final','La rúbrica señala semana 18; el catálogo y la planificación inicial usan semana 17. Confirmar fecha definitiva con el docente.')],[1.6,4.3])
sub('Guion propuesto para doce minutos')
p('Minutos 0 a 2: problema, alcance ficticio y evolución del Avance 1. Minutos 2 a 5: arquitectura, persistencia y diferencia entre privacidad de acceso y red privada. Minutos 5 a 8: demostración con usuario de prueba, recepción, estado y archivos. Minutos 8 a 10: resultados de carga, límites y seguridad. Minutos 10 a 12: costos, brechas y plan de cierre.')
p('La demostración positiva debe ensayarse antes de la sustentación, porque todavía no consta un recorrido completo con usuario confirmado en la evidencia posterior a Cognito. Se deben mostrar identificadores de solicitud y estados, nunca credenciales o tokens. Si una operación falla, corresponde explicar el resultado y su causa documentada, sin sustituirlo por una captura histórica presentada como ejecución nueva.')
sub('Criterio de finalización del proyecto')
p('El proyecto se considerará listo cuando el flujo autenticado sea reproducible, la orquestación exigida por el tema esté evidenciada, las pruebas funcionales y de carga alcancen los objetivos acordados, exista recuperación comprobada y se haya resuelto la correspondencia con los criterios de infraestructura y contenerización de la asignatura.')

z=doc.add_paragraph('12 1 SEGUIMIENTO DE SPRINTS HASTA LA SEMANA 12','A2H1');z.paragraph_format.page_break_before=True
p('Para el seguimiento del avance se agrupan las primeras doce semanas del WBS en seis sprints de dos semanas. Esta es una organización retrospectiva de entregables frente al plan académico, no un registro de fechas reales ni una afirmación de que se realizaron ceremonias Scrum. No se dispone de actas, tablero histórico ni velocidad medida por sprint.')
table(['Sprint y semanas','WBS asociado','Entregable y estado al corte'],[
('1\n1 a 2','1','Problema, justificación, objetivos SMART y alcance documentados en el Avance 1. No se adjunta acta de aprobación docente.'),
('2\n3 a 4','1.1 y 2','Selección de servicios, arquitectura conceptual, API y modelo DynamoDB documentados. La arquitectura implementada se actualiza en este avance.'),
('3\n5 a 6','2.1 y 3','Cuenta y permisos AWS, bucket privado y base de la recepción disponibles. El hito 2.1 está parcial: el repositorio Git de su evidencia sigue pendiente.'),
('4\n7 a 8','3 y 3.1','Recepción mediante API Gateway y Lambda, validación e idempotencia implementadas. Evidencia funcional histórica y pruebas Java disponibles.'),
('5\n9 a 10','3.2 e inicio de 3.3','Flujo DynamoDB Streams, Lambda publicadora, SQS y procesadora implementado. Reintentos y DLQ configurados; falta ensayo completo de fallos y redrive.'),
('6\n11 a 12','3.3 y 4\ninicio de 4.1','XML/PDF en S3 privado y consulta de estado disponibles. Logs y JWT incorporados. Falta validar el recorrido positivo completo después de Cognito.')],[1.0,1.0,3.9])
p('Las semanas indican la ubicación planificada del trabajo; el estado se sustenta en el código y las evidencias disponibles al 26 de octubre de 2026. Las actividades del WBS se superponen entre sprints: no se alteran sus rangos originales. La generación de archivos comienza en la semana 10 y se completa como entregable previsto en la 11.')
sub('Balance al cierre del hito')
p('Los entregables centrales de recepción, persistencia, procesamiento asíncrono, archivos y consulta están implementados. El hito de ambiente AWS no puede marcarse totalmente cerrado porque incluía un repositorio configurado. La seguridad y observabilidad de semanas 12 a 13 están iniciadas, y las pruebas previstas para semanas 13 a 15 ya tienen una primera ejecución con resultados mixtos. Las semanas no acreditan una velocidad ni un porcentaje de avance medido.')

z=doc.add_paragraph('12 2 TRABAJO ADICIONAL Y ACTIVIDADES PENDIENTES','A2H1');z.paragraph_format.page_break_before=True
sub('Ampliaciones y trabajo adelantado')
table(['Trabajo realizado','Relación con la línea base'],[
('Web desplegada en AWS','Frontend Angular y backend Java publicados por HTTPS; el uso de la aplicación no depende de localhost.'),
('Landing y diseño visual','Se incorporaron logo, página de presentación y rediseño de las pantallas de acceso.'),
('Identidad con Cognito','Registro, confirmación, ingreso, salida y recuperación de contraseña. La recuperación amplía el alcance inicial.'),
('Separación por usuario','JWT y propiedad de comprobantes; enlaces firmados para descargar archivos privados.'),
('Desacoplamiento adicional','Se pasó de dos funciones previstas a tres mediante una publicadora desde DynamoDB Streams.'),
('Pruebas y documentación anticipadas','21 pruebas Java, 12 del frontend, verificación pública y ensayos de carga; informe, diagramas y evidencias preparados antes del cierre del plan.')],[1.8,4.1])
p('Estas ampliaciones se registran como alcance adicional o trabajo adelantado, sin atribuirles una semana de ejecución no documentada. La publicación de CloudFront propia fue un intento bloqueado por verificación de cuenta; no se cuenta como logro desplegado.')
sub('Qué falta completar')
p('Para cerrar la validación del MVP: comprobar correo y confirmación de una cuenta propia, ejecutar el flujo positivo completo con JWT y verificar aislamiento entre dos usuarios. Para los hitos siguientes: resolver los errores de veinte solicitudes simultáneas, ensayar DLQ y reintentos, conservar métricas y logs correlacionados, y probar respaldo y restauración.')
p('Para completar el tema 10: implementar y demostrar la máquina de estados con Step Functions. Para resolver la rúbrica APF2: confirmar con el docente la adaptación serverless de VPC, VM y Docker o realizar lo que solicite. El repositorio Git con historial queda pendiente; GitHub se revisará más adelante según lo acordado. Después corresponde actualizar las evidencias y preparar la demostración final.')

h('13 EVIDENCIAS DEL SITIO PUBLICADO')
p('La aplicación se publica por HTTPS en https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/. Las capturas conservadas muestran la landing y el acceso incorporados después de la propuesta inicial. Los indicadores ilustrativos del diseño no se interpretan como métricas de DynamoDB ni como número real de operaciones.')
image(ROOT/'evidencias/nubixia-web-publicada.jpg','Figura A2 3. Landing publicada. Fuente: evidencia del proyecto nubixia-web-publicada.jpg.')
image(ROOT/'evidencias/nubixia-login-publicado.jpg','Figura A2 4. Pantalla de ingreso publicada. Fuente: nubixia-login-publicado.jpg.')
p('El registro dispone de una pantalla específica y se integra con Cognito. La existencia de la vista y las respuestas negativas del servicio no acreditan entrega del correo ni confirmación satisfactoria de un nuevo usuario; esa comprobación figura entre las validaciones pendientes.',True)

h('14 EVIDENCIAS DEL PROCESAMIENTO Y TRAZABILIDAD')
image(ROOT/'evidencias/aws-comprobante-aceptado.jpg','Figura A2 5. Comprobante ficticio aceptado en una prueba anterior a Cognito. Es evidencia histórica y no una sesión nueva del flujo autenticado.')
table(['Archivo de evidencia','Contenido y límite de interpretación'],[
('aws-flujo-escolar.json','Veinte recepciones con concurrencia dos, tiempos, idempotencia y archivos. Flujo histórico con API key.'),
('aws-arranque-frio.json','Ráfaga fría con errores HTTP; no acredita el objetivo de veinte simultáneas.'),
('aws-rafaga-20.json','Ráfaga caliente con trece recepciones de veinte.'),
('aws-web-publica.json','Diez comprobaciones públicas y respuestas negativas de autenticación posteriores a Cognito.'),
('Reportes Surefire','Resultados de las pruebas Java disponibles en target/surefire-reports.')],[2.1,3.8])
p('La plantilla declara los grupos de CloudWatch y su retención de tres días. No se adjunta una exportación reciente de logs ni un panel de métricas como si hubieran sido capturados en esta revisión. Para la siguiente entrega se deben conservar logs anonimizados con fecha, versión e identificadores de correlación que vinculen la recepción, el mensaje y el resultado.')

h('15 CONCLUSIONES Y REFERENCIAS')
p('Nubixia avanzó desde una propuesta de recepción asíncrona hacia una implementación con web, identidad y persistencia administradas. DynamoDB conserva los comprobantes y S3 los documentos derivados; Lambda y SQS separan la recepción del procesamiento. La evidencia disponible confirma el flujo escolar en concurrencia reducida y deja visibles los errores de ráfaga.')
p('El enfoque serverless permite una demostración de bajo consumo, aunque no garantiza gratuidad. La entrega no acredita todavía todos los criterios literales del APF2: faltan VPC y VM solicitadas, Docker, trazabilidad Git y la orquestación Step Functions del catálogo. El siguiente trabajo debe resolver esas brechas y validar el recorrido positivo con Cognito, la carga objetivo y la recuperación.')
sub('Referencias y fuentes de evidencia')
refs=[
('1','Rúbricas de Servicios Cloud. APF2 semana 12, APF3 semana 17 y entrega final. Documento proporcionado por la asignatura.',''),
('2','Temas Proyecto Final de Servicios Cloud. Área 5 tema 10. Documento proporcionado por la asignatura.',''),
('3','Vera Jara A P J. Avance Proyecto 1. 27 de agosto de 2026. Parte inicial conservada de este informe.',''),
('4','AWS. Configuración de funciones Lambda para acceder a una VPC.','https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html'),
('5','AWS. Precios de Lambda.','https://aws.amazon.com/lambda/pricing/'),
('6','AWS. Precios de API Gateway.','https://aws.amazon.com/api-gateway/pricing/'),
('7','AWS. Precios de DynamoDB.','https://aws.amazon.com/dynamodb/pricing/'),
('8','AWS. Precios de Amazon S3.','https://aws.amazon.com/s3/pricing/'),
('9','AWS. Precios de Amazon SQS.','https://aws.amazon.com/sqs/pricing/'),
('10','AWS. Precios de CloudWatch.','https://aws.amazon.com/cloudwatch/pricing/'),
('11','AWS. Precios de Cognito.','https://aws.amazon.com/cognito/pricing/'),
('12','Código fuente, plantilla CloudFormation, guías de docs y evidencias JSON/JPG del proyecto Nubixia. Revisión documental del 26 de octubre de 2026.','')]
for n,label,url in refs:
    z=p(f'[{n}] {label}',True)
    if url:
        z.add_run(' ')
        rel=doc.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
        a=OxmlElement('w:hyperlink');a.set(qn('r:id'),rel)
        r=OxmlElement('w:r');pr=OxmlElement('w:rPr');c=OxmlElement('w:color');c.set(qn('w:val'),'000000');pr.append(c);u=OxmlElement('w:u');u.set(qn('w:val'),'single');pr.append(u);r.append(pr)
        t=OxmlElement('w:t');t.text=url;r.append(t);a.append(r);z._p.append(a)
p('Las tarifas son referencias consultadas en la fecha de corte y pueden cambiar. Los archivos originales de la asignatura prevalecen para la evaluación; las interpretaciones y el plan de cierre de esta continuación son responsabilidad del proyecto.',True)

assert [canon(e) for e in list(doc._element.body)[:len(original)]]==original,'Original body changed'
working=TMP/'combined-working.docx';doc.save(working)
allowed={'word/document.xml','word/styles.xml','word/settings.xml','word/_rels/document.xml.rels','[Content_Types].xml'}
with ZipFile(REF) as r,ZipFile(working) as w,ZipFile(OUT,'w',ZIP_DEFLATED) as out:
    for name in w.namelist():out.writestr(name,r.read(name) if name in r.namelist() and name not in allowed else w.read(name))
with ZipFile(REF) as r,ZipFile(OUT) as out:
    opaque=all(r.read(n)==out.read(n) for n in r.namelist() if n not in allowed)
    root=etree.fromstring(out.read('word/document.xml'))
    body=root.find(qn('w:body'))
    assert [canon(e) for e in list(body)[:len(original)]]==original
    assert opaque
pres={'original_body_elements_preserved':len(original),'opaque_parts_identical':opaque,'source_sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'output':str(OUT)}
(TMP/'preservation.json').write_text(json.dumps(pres,indent=2),encoding='utf-8')
(TMP/'bookmarks.json').write_text(json.dumps(heads,ensure_ascii=False),encoding='utf-8')
print(json.dumps(pres,indent=2))
