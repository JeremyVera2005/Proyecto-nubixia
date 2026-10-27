import { Component, OnInit, OnDestroy, computed, signal, inject, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from './auth.service';

interface Item { descripcion: string; cantidad: number; precioUnitario: number; }
interface Invoice { rucEmisor: string; cliente: string; fecha: string; serie: string; numero: string; items: Item[]; subtotal: number; igv: number; total: number; }
interface Document { documentId: string; estado: string; comprobante: Invoice; creadoEn: string; actualizadoEn: string; error: string | null; archivosDisponibles: boolean; historial: { estado: string; fecha: string; detalle: string }[]; duplicado?: boolean; }

@Component({ selector: 'app-workspace', imports: [CommonModule, FormsModule], templateUrl: './app.html', styleUrl: './app.css' })
export class App implements OnInit, OnDestroy {
 readonly auth=inject(AuthService);
 readonly signedOut=output<void>();
 useAuth=false;
 readonly documents = signal<Document[]>([]);
 readonly selected = signal<Document | null>(null);
 readonly page = signal<'dashboard' | 'new' | 'settings'>('dashboard');
 readonly busy = signal(false);
 readonly loading = signal(false);
 readonly error = signal('');
 readonly notice = signal('');
 readonly connected = signal(false);
 readonly cloudMode = signal(false);
 readonly downloading = signal('');
 readonly search = signal('');
 readonly status = signal('');
 readonly accepted = computed(() => this.documents().filter(d => d.estado === 'ACEPTADO').length);
 readonly pending = computed(() => this.documents().filter(d => ['RECIBIDO', 'PROCESANDO'].includes(d.estado)).length);
 readonly totalIssued = computed(() => this.documents().filter(d => d.estado === 'ACEPTADO').reduce((n, d) => n + Number(d.comprobante.total), 0));
 readonly filtered = computed(() => {
  const q = this.search().toLowerCase();
  return this.documents().filter(d => (!this.status() || d.estado === this.status()) &&
   (d.comprobante.cliente + d.documentId + d.comprobante.serie + '-' + d.comprobante.numero).toLowerCase().includes(q));
 });
 apiUrl = 'http://localhost:8080';
 apiKey = '';
 form: Invoice = this.empty();
 private timer?: ReturnType<typeof setInterval>;
 private refreshing = false;
 private automaticConnection = false;
 private abort = new AbortController();
 private empty(): Invoice {
  const today = new Date();
  const date = [today.getFullYear(), String(today.getMonth()+1).padStart(2,'0'), String(today.getDate()).padStart(2,'0')].join('-');
  return { rucEmisor: '', cliente: '', fecha: date, serie: 'F001', numero: '', items: [{ descripcion: '', cantidad: 1, precioUnitario: 0 }], subtotal: 0, igv: 0, total: 0 };
 }
 async ngOnInit() {
  let autoConnectLocal = true;
  let localProxy = false;
  try {
   const config = await fetch(new URL('config.json',document.baseURI).pathname).then(r => r.json());
   this.apiUrl = config.apiUrl || this.apiUrl;
   if(config.auth) { this.auth.configure(config.auth);this.useAuth=true;this.cloudMode.set(true); }
   autoConnectLocal = config.autoConnectLocal !== false;
   localProxy = config.localProxy === true && config.apiUrl === '/api';
   this.cloudMode.set(this.useAuth || config.cloudMode === true);
  } catch { /* Use the local development defaults if runtime config is unavailable. */ }
  if (!localProxy && !this.useAuth) this.apiUrl = sessionStorage.getItem('nubixia-api-url') || this.apiUrl;
  this.apiKey = this.useAuth ? 'cognito' : sessionStorage.getItem('nubixia-api-key') || '';
  const loopback = new Set(['localhost', '127.0.0.1', '[::1]']);
  if (localProxy && loopback.has(window.location.hostname)) {
   this.apiKey = 'local-proxy';
   this.automaticConnection = true;
  }
  let localApi = false;
  try { localApi = loopback.has(new URL(this.apiUrl).hostname); } catch {}
  // This public demo credential must only be used for a local frontend and local API.
  if (!this.apiKey && autoConnectLocal && localApi && loopback.has(window.location.hostname)) {
   this.apiKey = 'nubixia-demo-local-2026';
   this.automaticConnection = true;
  }
  if (this.apiKey) await this.refresh();
  else this.page.set('settings');
  if (this.abort.signal.aborted) return;
  this.timer = setInterval(() => {
   if (this.cloudMode() && this.connected() && this.pending() === 0) return;
   if (this.apiKey && (this.connected() || this.automaticConnection)) void this.refresh(true);
  }, 5000);
 }
 ngOnDestroy() { clearInterval(this.timer); this.abort.abort(); }
 private async request(path: string, options: RequestInit = {}): Promise<Response> {
  let response: Response;
  for (let attempt = 0; ; attempt++) {
   response = await fetch(this.apiUrl.replace(/\/$/, '') + path, {
    ...options, signal: this.abort.signal, headers: { ...(this.useAuth ? {'Authorization':await this.auth.token()} : {'X-API-Key':this.apiKey}), ...(options.body ? { 'Content-Type': 'application/json' } : {}) }
   });
   if (!this.cloudMode() || attempt >= 3 || ![429, 500, 502, 503, 504].includes(response.status)) break;
   // POST uses a deterministic document ID, so retrying the same payload is safe.
   await new Promise<void>(resolve => setTimeout(resolve, 500 * 2 ** attempt + Math.random() * 250));
   this.abort.signal.throwIfAborted();
  }
  if (!response.ok) {
   let message = 'No se pudo completar la solicitud (' + response.status + ')';
   try { const data = await response.json(); message = data.mensaje || data.message || message; } catch {}
   if ([401, 403].includes(response.status)) this.connected.set(false);
   if(this.useAuth && response.status===401) {this.auth.clear();this.signedOut.emit();}
   throw new Error(message);
  }
  return response;
 }
 async connect() {
  this.error.set(''); this.notice.set('');
  try {
   const url = new URL(this.apiUrl);
   if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error();
  } catch { this.error.set('Ingresa una URL http o https válida, sin credenciales ni parámetros.'); return; }
  if (!this.apiKey.trim()) { this.error.set('Ingresa tu API key.'); return; }
  this.apiUrl = this.apiUrl.replace(/\/+$/, ''); this.apiKey = this.apiKey.trim();
  sessionStorage.setItem('nubixia-api-url', this.apiUrl); sessionStorage.setItem('nubixia-api-key', this.apiKey);
  await this.refresh();
  if (this.connected()) { this.page.set('dashboard'); this.notice.set('Conexión establecida.'); }
 }
 disconnect() {
  this.automaticConnection = false;
  sessionStorage.removeItem('nubixia-api-key'); this.apiKey = ''; this.connected.set(false);
  this.documents.set([]); this.selected.set(null); this.page.set('settings');
 }
 async refresh(silent = false) {
  if (this.refreshing) return;
  this.refreshing = true; if (!silent) { this.loading.set(true); this.error.set(''); }
  try {
   const data = await (await this.request('/comprobantes')).json();
   if (!this.connected()) this.error.set('');
   this.documents.set(data.items); this.connected.set(true);
   const selected = this.selected();
   if (selected) this.selected.set(data.items.find((d: Document) => d.documentId === selected.documentId) || selected);
  } catch (e) { this.error.set(this.message(e)); this.connected.set(false); }
  finally { this.loading.set(false); this.refreshing = false; }
 }
 round(value: number) { return Math.round((value + Number.EPSILON) * 100) / 100; }
 get subtotal() { return this.round(this.form.items.reduce((sum, i) => sum + this.round(Number(i.cantidad) * Number(i.precioUnitario)), 0)); }
 get igv() { return this.round(this.subtotal * 0.18); }
 get total() { return this.round(this.subtotal + this.igv); }
 addItem() { if (this.form.items.length < 100) this.form.items.push({ descripcion: '', cantidad: 1, precioUnitario: 0 }); }
 removeItem(index: number) { if (this.form.items.length > 1) this.form.items.splice(index, 1); }
 newInvoice() { this.form = this.empty(); this.error.set(''); this.notice.set(''); this.selected.set(null); this.page.set('new'); }
 async submit() {
  if (this.busy()) return;
  this.busy.set(true); this.error.set(''); this.notice.set('');
  try {
   const payload = { ...this.form, subtotal: this.subtotal, igv: this.igv, total: this.total,
    items: this.form.items.map(i => ({ ...i, cantidad: Number(i.cantidad), precioUnitario: Number(i.precioUnitario) })) };
   const doc: Document = await (await this.request('/comprobantes', { method: 'POST', body: JSON.stringify(payload) })).json();
   this.notice.set(doc.duplicado ? 'Este comprobante ya estaba registrado. Se ha recuperado el original.' : 'Comprobante recibido. Los archivos se están generando.');
   this.selected.set(doc); this.page.set('dashboard'); await this.refresh();
  } catch (e) { this.error.set(this.message(e)); }
  finally { this.busy.set(false); }
 }
 async consult(id: string) {
  this.error.set('');
  if (!id.trim()) return;
  try { this.selected.set(await (await this.request('/comprobantes/' + encodeURIComponent(id.trim()))).json()); }
  catch (e) { this.error.set(this.message(e)); }
 }
 async download(doc: Document, extension: 'xml' | 'pdf') {
  this.downloading.set(extension); this.error.set('');
  try {
   let response = await this.request('/comprobantes/' + doc.documentId + '/archivos/' + extension);
   if (response.headers.get('Content-Type')?.includes('application/json')) {
    const download = await response.json();
    response = await fetch(download.url, { signal: this.abort.signal });
    if (!response.ok) throw new Error('No se pudo descargar el archivo. Vuelve a consultar el estado.');
   }
   const url = URL.createObjectURL(await response.blob());
   const a = document.createElement('a'); a.href = url; a.download = doc.comprobante.serie + '-' + doc.comprobante.numero + '.' + extension;
   a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (e) { this.error.set(this.message(e)); }
  finally { this.downloading.set(''); }
 }
 private message(e: unknown): string { return e instanceof TypeError ? 'No se pudo conectar con la API. Verifica la URL, que el backend esté iniciado y el origen CORS.' : e instanceof Error ? e.message : 'Ocurrió un error inesperado.'; }
}
