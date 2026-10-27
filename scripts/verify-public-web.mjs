import {writeFile,mkdir} from 'node:fs/promises';
const base='https://0qx6ww77nl.execute-api.us-east-2.amazonaws.com/demo/';
const results=[];
const check=(name,ok,detail)=>{results.push({name,ok,detail});if(!ok)console.error(name,detail);};
try {
 const home=await fetch(base);const html=await home.text();
 check('Landing HTTPS publica',home.status===200 && html.includes('<app-root>') && html.includes('<base href="/demo/">'),home.status);
 check('Cabeceras de seguridad',home.headers.get('x-content-type-options')==='nosniff' && home.headers.get('content-security-policy')?.includes("frame-ancestors 'none'"));
 const style=html.match(/href="(styles-[A-Za-z0-9]+\.css)"/)?.[1];
 const styleResponse=style?await fetch(base+style):null;
 check('CSS completo sin manejadores inline bloqueados por CSP',!!styleResponse?.ok && !html.includes('onload='),styleResponse?.status);
 const configResponse=await fetch(base+'config.json');const config=await configResponse.json();
 check('Configuracion Cognito sin clave compartida',configResponse.ok && config.auth?.userPoolId==='us-east-2_kJ2s3wLov' && !!config.auth?.clientId && !JSON.stringify(config).includes('apiKey'));
 const script=html.match(/src="(main-[A-Za-z0-9]+\.js)"/)?.[1];
 if(script){const r=await fetch(base+script);check('JavaScript publicado',r.ok && r.headers.get('content-type')?.includes('javascript'),r.status);}
 else check('JavaScript publicado',false,'No se encontro el bundle');
 const logo=await fetch(base+'nubixia-logo.png');const bytes=new Uint8Array(await logo.arrayBuffer());
 check('Logo PNG publicado',logo.ok && bytes[0]===137 && bytes[1]===80 && bytes[2]===78,bytes.length);
 const unauth=await fetch(base+'comprobantes');check('Datos protegidos sin sesion',[401,403].includes(unauth.status),unauth.status);
 const invalid=await fetch(base+'comprobantes',{headers:{Authorization:'invalid-token'}});check('Token inventado rechazado',[401,403].includes(invalid.status),invalid.status);
 const cognito=async(action,data)=>fetch('https://cognito-idp.us-east-2.amazonaws.com/',{method:'POST',headers:{'Content-Type':'application/x-amz-json-1.1','X-Amz-Target':'AWSCognitoIdentityProviderService.'+action},body:JSON.stringify(data)});
 if(config.auth?.clientId){
  const login=await cognito('InitiateAuth',{ClientId:config.auth.clientId,AuthFlow:'USER_PASSWORD_AUTH',AuthParameters:{USERNAME:'verification-no-account@example.invalid',PASSWORD:'NotARealPassword123'}});const data=await login.json();
  check('Login Cognito real rechaza datos incorrectos',login.status===400 && data.__type==='NotAuthorizedException',data.__type);
  const signup=await cognito('SignUp',{ClientId:config.auth.clientId,Username:'verification-no-account@example.invalid',Password:'bad'});const signupData=await signup.json();
  check('Registro real valida contrasena antes de crear cuenta',signup.status===400 && signupData.__type==='InvalidPasswordException',signupData.__type);
 }
}catch(e){check('Verificacion completa',false,String(e));}
await mkdir('evidencias',{recursive:true});await writeFile('evidencias/aws-web-publica.json',JSON.stringify({date:new Date().toISOString(),url:base,results},null,2));
console.log(JSON.stringify(results,null,2));if(results.some(r=>!r.ok))process.exitCode=1;
