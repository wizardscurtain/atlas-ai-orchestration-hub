require('dotenv').config();

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const target = process.env.REACT_APP_BACKEND_URL;

if (!target) {
  throw new Error('Missing REACT_APP_BACKEND_URL in /app/frontend/.env');
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

const port = Number(process.env.PORT || 3000);
const host = process.env.HOST || '0.0.0.0';

app.listen(port, host, () => {
  console.log(`Atlas preview proxy listening on http://${host}:${port}`);
});
