import { TestBed } from '@angular/core/testing';
import { App } from './app';
import { vi } from 'vitest';

describe('Nubixia', () => {
 beforeEach(async () => {
  sessionStorage.clear();
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => ({
   ok: true, json: async () => url === '/config.json'
    ? { apiUrl: 'http://localhost:8080', autoConnectLocal: true } : { items: [] }
  })));
  await TestBed.configureTestingModule({ imports: [App] }).compileComponents();
 });
 afterEach(() => { vi.unstubAllGlobals(); });
 it('conecta automáticamente con la API local sin pedir credenciales', async () => {
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.connected()).toBe(true));
  fixture.detectChanges();
  expect(fixture.componentInstance.page()).toBe('dashboard');
  expect(fixture.nativeElement.querySelector('h1')?.textContent).toContain('Comprobantes');
  expect(fetch).toHaveBeenCalledWith('http://localhost:8080/comprobantes', expect.objectContaining({
   headers: { 'X-API-Key': 'nubixia-demo-local-2026' }
  }));
  fixture.destroy();
 });
 it('conecta al proxy AWS sin exponer la clave privada ni conservar la URL local anterior', async () => {
  sessionStorage.setItem('nubixia-api-url', 'http://localhost:8080');
  sessionStorage.setItem('nubixia-api-key', 'clave-anterior');
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => ({
   ok: true, json: async () => url === '/config.json'
    ? { apiUrl: '/api', localProxy: true, cloudMode: true } : { items: [] }
  })));
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.connected()).toBe(true));
  expect(fixture.componentInstance.cloudMode()).toBe(true);
  expect(fetch).toHaveBeenCalledWith('/api/comprobantes', expect.objectContaining({
   headers: { 'X-API-Key': 'local-proxy' }
  }));
  fixture.destroy();
 });
 it('reintenta una saturación temporal de AWS y recupera la conexión', async () => {
  vi.stubGlobal('fetch', vi.fn()
   .mockResolvedValueOnce({ok:true,json:async()=>({apiUrl:'/api',localProxy:true,cloudMode:true})})
   .mockResolvedValueOnce({ok:false,status:500})
   .mockResolvedValueOnce({ok:true,status:200,json:async()=>({items:[]})}));
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.connected()).toBe(true), {timeout:2000});
  expect(fetch).toHaveBeenCalledTimes(3);
  fixture.destroy();
 });
 it('no envía la credencial de demo a una API remota', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok: true, json: async () => ({
   apiUrl: 'https://api.example.com', autoConnectLocal: true
  })}));
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.page()).toBe('settings'));
  expect(fixture.componentInstance.apiKey).toBe('');
  expect(fetch).toHaveBeenCalledTimes(1);
  fixture.destroy();
 });
 it('respeta la desactivación de conexión automática', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok: true, json: async () => ({
   apiUrl: 'http://localhost:8080', autoConnectLocal: false
  })}));
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.page()).toBe('settings'));
  expect(fetch).toHaveBeenCalledTimes(1);
  fixture.destroy();
 });
 it('conserva la credencial personalizada de la sesión', async () => {
  sessionStorage.setItem('nubixia-api-key', 'clave-personalizada');
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.connected()).toBe(true));
  expect(fixture.componentInstance.apiKey).toBe('clave-personalizada');
  expect(fetch).toHaveBeenCalledWith('http://localhost:8080/comprobantes', expect.objectContaining({
   headers: { 'X-API-Key': 'clave-personalizada' }
  }));
  fixture.destroy();
 });
 it('mantiene el resumen y permite reintentar si el backend está apagado', async () => {
  vi.stubGlobal('fetch', vi.fn()
   .mockResolvedValueOnce({ok:true,json:async()=>({apiUrl:'http://localhost:8080'})})
   .mockRejectedValueOnce(new TypeError('Failed to fetch'))
   .mockResolvedValueOnce({ok:true,json:async()=>({items:[]})}));
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  await vi.waitFor(() => expect(fixture.componentInstance.error()).not.toBe(''));
  expect(fixture.componentInstance.page()).toBe('dashboard');
  await fixture.componentInstance.refresh();
  expect(fixture.componentInstance.connected()).toBe(true);
  expect(fixture.componentInstance.error()).toBe('');
  fixture.destroy();
 });
 it('calcula cada línea, IGV y total con redondeo monetario', () => {
  const fixture = TestBed.createComponent(App);
  const app = fixture.componentInstance;
  app.form.items = [{ descripcion: 'Servicio', cantidad: 2, precioUnitario: 50 }];
  expect(app.subtotal).toBe(100); expect(app.igv).toBe(18); expect(app.total).toBe(118);
  app.form.items = [{ descripcion: 'Fracción', cantidad: 3, precioUnitario: 0.1 }];
  expect(app.total).toBe(0.35); fixture.destroy();
 });
 it('recupera el comprobante original cuando la API indica duplicado', async () => {
  const fixture = TestBed.createComponent(App);
  const app = fixture.componentInstance;
  const doc = { documentId: 'a'.repeat(64), estado: 'RECIBIDO', comprobante: app.form, historial: [], duplicado: true };
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => doc })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ items: [doc] }) }));
  await app.submit();
  expect(app.notice()).toContain('ya estaba registrado'); expect(app.selected()?.documentId).toBe(doc.documentId);
  fixture.destroy();
 });
});
