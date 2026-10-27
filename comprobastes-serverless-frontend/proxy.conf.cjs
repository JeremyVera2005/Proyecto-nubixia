const fs = require('node:fs');
const path = require('node:path');
const configPath = path.resolve(__dirname, '../.env.aws.json');
let config = {};
if (fs.existsSync(configPath)) config = JSON.parse(fs.readFileSync(configPath, 'utf8').replace(/^\uFEFF/, ''));
const apiUrl = process.env.NUBIXIA_AWS_API_URL || config.apiUrl;
const apiKey = process.env.NUBIXIA_AWS_API_KEY || config.apiKey;
if (!apiUrl || !apiKey) {
 module.exports = {};
} else {
 const target = new URL(apiUrl);
 if (target.protocol !== 'https:' || !target.hostname.endsWith('.execute-api.us-east-2.amazonaws.com') ||
     target.username || target.password || target.search || target.hash) {
  throw new Error('La API de la demo debe ser un endpoint HTTPS de API Gateway en Ohio.');
 }
 module.exports = {
  '/api/**': {
   target: target.origin,
   secure: true,
   changeOrigin: true,
   rewrite: requestPath => target.pathname.replace(/\/$/, '') + requestPath.replace(/^\/api/, ''),
   headers: { 'X-API-Key': apiKey }
  }
 };
}
