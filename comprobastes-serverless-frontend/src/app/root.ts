import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { App } from './app';
import { AuthService } from './auth.service';
@Component({selector:'app-root',imports:[FormsModule,App],templateUrl:'./root.html',styleUrl:'./root.css'})
export class Root implements OnInit {
 readonly auth=inject(AuthService);
 readonly view=signal<'landing'|'login'|'register'|'confirm'|'forgot'|'reset'|'workspace'>('landing');
 readonly busy=signal(false); readonly ready=signal(false); readonly error=signal(''); readonly notice=signal('');
 email=''; password=''; name=''; code=''; passwordAgain='';
 readonly local=['localhost','127.0.0.1','[::1]'].includes(location.hostname);
 async ngOnInit() {
  try {
   const response=await fetch(new URL('config.json',document.baseURI).pathname); if(!response.ok) throw new Error('No se pudo cargar la configuración.');
   const config=await response.json(); this.auth.configure(config.auth);
   if(this.auth.session()) { await this.auth.token(); this.view.set('workspace'); }
  } catch(e) { this.auth.clear(); this.error.set(e instanceof Error?e.message:'No se pudo recuperar la sesión.'); }
  finally { this.ready.set(true); }
 }
 go(view:'landing'|'login'|'register'|'confirm'|'forgot'|'reset') { this.view.set(view);this.error.set('');this.notice.set('');this.password='';this.passwordAgain='';this.code='';window.scrollTo(0,0); }
 async submit() {
  if(this.busy()) return;
  this.busy.set(true);this.error.set('');this.notice.set('');this.email=this.email.trim().toLowerCase();
  try {
   switch(this.view()) {
    case 'register':
     if(this.password!==this.passwordAgain) throw new Error('Las contraseñas no coinciden.');
     await this.auth.register(this.email,this.password,this.name.trim());this.view.set('confirm');this.notice.set('Te enviamos un código al correo. Ingrésalo para activar tu cuenta.');break;
    case 'confirm': await this.auth.confirm(this.email,this.code.trim());this.view.set('login');this.notice.set('Correo confirmado. Ya puedes iniciar sesión.');break;
    case 'login': await this.auth.login(this.email,this.password);this.view.set('workspace');break;
    case 'forgot': await this.auth.forgot(this.email);this.view.set('reset');this.notice.set('Si existe una cuenta, recibirás un código de recuperación.');break;
    case 'reset': await this.auth.reset(this.email,this.code.trim(),this.password);this.view.set('login');this.notice.set('Contraseña actualizada. Inicia sesión.');break;
   }
  } catch(e) {
   if((e as any)?.code==='UserNotConfirmedException') this.view.set('confirm');
   this.error.set(e instanceof Error?e.message:'No se pudo completar la operación.');
  } finally {this.password='';this.passwordAgain='';this.busy.set(false);}
 }
 async resend() {this.busy.set(true);try{await this.auth.resend(this.email);this.notice.set('Código reenviado. Revisa tu correo.');}catch(e){this.error.set((e as Error).message);}finally{this.busy.set(false);}}
 async logout() {await this.auth.logout();this.view.set('landing');this.email='';this.password='';}
}
