require('dotenv').config();

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const target = process.env.BACKEND_PROXY_TARGET;
const port = process.env.PORT;
const host = process.env.HOST;

if (!target) {
  throw new Error('Missing BACKEND_PROXY_TARGET in /app/frontend/.env');
}

if (!port || !host) {
  throw new Error('Missing HOST or PORT environment variables for the preview proxy');
}

const app = express();

app.disable('x-powered-by');
app.set('trust proxy', true);

app.use(
  '/',
  createProxyMiddleware({
    target,
    changeOrigin: true,
    ws: false,
    xfwd: true,
    proxyTimeout: 30000,
    timeout: 30000,
    onError(err, req, res) {
      res.status(502).send('Atlas preview proxy could not reach the backend.');
    },
  })
);

app.listen(Number(port), host, () => {
  console.log(`Atlas preview proxy listening on http://${host}:${port}`);
});
