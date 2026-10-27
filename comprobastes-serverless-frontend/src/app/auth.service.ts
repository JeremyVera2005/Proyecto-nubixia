import { Injectable, signal } from '@angular/core';

export interface AuthConfig { region: string; userPoolId: string; clientId: string; }
interface Session { id: string; refresh: string; email: string; expires: number; }
@Injectable({providedIn:'root'})
export class AuthService {
 readonly session = signal<Session | null>(null);
 config: AuthConfig | null = null;
 private refreshing?: Promise<string>;
 configure(config?: AuthConfig) {
  if (!config) return;
  if (config.region !== 'us-east-2' || !/^us-east-2_[A-Za-z0-9]+$/.test(config.userPoolId) || !/^[a-z0-9]+$/.test(config.clientId)) throw new Error('Configuración de acceso inválida.');
  this.config=config;
  try { const saved=JSON.parse(sessionStorage.getItem('nubixia-session') || 'null'); if(saved?.id && saved?.refresh && typeof saved.expires==='number') this.session.set(saved); } catch { sessionStorage.removeItem('nubixia-session'); }
 }
 async call(action: string, data: object): Promise<any> {
  if(!this.config) throw new Error('El acceso estará disponible cuando se publique la configuración de Cognito.');
  const response=await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`,{
   method:'POST',headers:{'Content-Type':'application/x-amz-json-1.1','X-Amz-Target':`AWSCognitoIdentityProviderService.${action}`},body:JSON.stringify(data)
  });
  const result=await response.json();
  if(!response.ok) {
   const code=String(result.__type || '').split('#').pop();
   const messages:Record<string,string>={NotAuthorizedException:'Correo o contraseña incorrectos, o sesión vencida.',UserNotFoundException:'No se pudo acceder con esos datos.',UsernameExistsException:'Ya existe una cuenta con ese correo. Inicia sesión o recupera tu contraseña.',InvalidPasswordException:'Usa al menos 10 caracteres, mayúscula, minúscula y número.',CodeMismatchException:'El código no es correcto. Revísalo e inténtalo de nuevo.',ExpiredCodeException:'El código venció. Solicita uno nuevo.',LimitExceededException:'Se alcanzó el límite temporal. Inténtalo más tarde.',TooManyRequestsException:'Demasiados intentos. Espera un momento.',UserNotConfirmedException:'Confirma tu correo para ingresar.',InvalidParameterException:'Revisa el correo y los datos ingresados.'};
   const error=new Error(messages[code || ''] || 'No se pudo completar la operación. Inténtalo de nuevo.');
   Object.assign(error,{code}); throw error;
  }
  return result;
 }
 async register(email:string,password:string,name:string) { return this.call('SignUp',{ClientId:this.config?.clientId,Username:email,Password:password,UserAttributes:[{Name:'email',Value:email},{Name:'name',Value:name}]}); }
 async confirm(email:string,code:string) { await this.call('ConfirmSignUp',{ClientId:this.config?.clientId,Username:email,ConfirmationCode:code}); }
 async resend(email:string) { await this.call('ResendConfirmationCode',{ClientId:this.config?.clientId,Username:email}); }
 private save(result:any,email:string,refresh?:string) {
  const session={id:result.IdToken,refresh:result.RefreshToken || refresh,email,expires:Date.now()+Number(result.ExpiresIn)*1000};
  if(!session.id || !session.refresh || !Number.isFinite(session.expires)) throw new Error('Respuesta de sesión inválida.');
  this.session.set(session); sessionStorage.setItem('nubixia-session',JSON.stringify(session));
 }
 async login(email:string,password:string) {
  const result=await this.call('InitiateAuth',{ClientId:this.config?.clientId,AuthFlow:'USER_PASSWORD_AUTH',AuthParameters:{USERNAME:email,PASSWORD:password}});
  if(!result.AuthenticationResult) throw new Error('Tu cuenta requiere completar un paso adicional de acceso.');
  this.save(result.AuthenticationResult,email);
 }
 async token():Promise<string> {
  const session=this.session(); if(!session) throw new Error('Inicia sesión para continuar.');
  if(session.expires>Date.now()+60000) return session.id;
  if(this.refreshing) return this.refreshing;
  this.refreshing=this.call('InitiateAuth',{ClientId:this.config?.clientId,AuthFlow:'REFRESH_TOKEN_AUTH',AuthParameters:{REFRESH_TOKEN:session.refresh}})
   .then(r=>{this.save(r.AuthenticationResult,session.email,session.refresh);return this.session()!.id;})
   .catch(e=>{this.clear();throw e;}).finally(()=>{this.refreshing=undefined;});
  return this.refreshing;
 }
 async forgot(email:string) { await this.call('ForgotPassword',{ClientId:this.config?.clientId,Username:email}); }
 async reset(email:string,code:string,password:string) { await this.call('ConfirmForgotPassword',{ClientId:this.config?.clientId,Username:email,ConfirmationCode:code,Password:password}); }
 clear() { this.session.set(null);sessionStorage.removeItem('nubixia-session'); }
 async logout() {
  const refresh=this.session()?.refresh; this.clear();
  if(refresh) try { await this.call('RevokeToken',{ClientId:this.config?.clientId,Token:refresh}); } catch { /* Local credentials are already cleared. */ }
 }
}
