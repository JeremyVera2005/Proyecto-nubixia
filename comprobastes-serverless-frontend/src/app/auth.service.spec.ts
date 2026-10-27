import { describe, it, expect, vi, afterEach } from 'vitest';
import { AuthService } from './auth.service';
const config={region:'us-east-2',userPoolId:'us-east-2_TestPool',clientId:'abc123'};
afterEach(()=>{sessionStorage.clear();vi.unstubAllGlobals();});
describe('Autenticación Cognito',()=>{
 it('no conserva contraseñas y registra una sesión con vencimiento',async()=>{
  const auth=new AuthService();auth.configure(config);
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({AuthenticationResult:{IdToken:'signed-id-token',RefreshToken:'refresh-token',ExpiresIn:900}})}));
  await auth.login('test@example.com','Password123');
  expect(await auth.token()).toBe('signed-id-token');
  expect(sessionStorage.getItem('nubixia-session')).not.toContain('Password123');
  expect(fetch).toHaveBeenCalledWith('https://cognito-idp.us-east-2.amazonaws.com/',expect.objectContaining({method:'POST'}));
 });
 it('renueva una sola vez solicitudes concurrentes y limpia una sesión rechazada',async()=>{
  sessionStorage.setItem('nubixia-session',JSON.stringify({id:'expired',refresh:'refresh-token',email:'test@example.com',expires:0}));
  const auth=new AuthService();auth.configure(config);
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({__type:'NotAuthorizedException'})}));
  const results=await Promise.allSettled([auth.token(),auth.token()]);
  expect(results.every(r=>r.status==='rejected')).toBe(true);
  expect(fetch).toHaveBeenCalledTimes(1);expect(auth.session()).toBeNull();
  expect(sessionStorage.getItem('nubixia-session')).toBeNull();
 });
 it('no simula un registro exitoso si Cognito rechaza la solicitud',async()=>{
  const auth=new AuthService();auth.configure(config);
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({__type:'UsernameExistsException'})}));
  await expect(auth.register('test@example.com','Password123','Prueba')).rejects.toThrow('Ya existe una cuenta');
  expect(auth.session()).toBeNull();
 });
});
