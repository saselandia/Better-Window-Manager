/* BWM Stremio Linux integration. Loaded only into its bundled Node server.
 * Add a stylesheet to the existing same-origin web UI; do not modify Flatpak files,
 * change the web UI origin (session storage), or intercept media/API responses.
 */
'use strict';
const http = require('node:http');
const fs = require('node:fs');
const zlib = require('node:zlib');
const ROOT = '/__bwm_theme';
const MARKER = 'data-bwm-theme';
const client = `(() => {
    if (window.__bwmTheme) return;
    window.__bwmTheme = true;
    const style = document.createElement('style');
    style.id = 'bwm-theme';
    document.head.append(style);
    let busy = false;
    async function refresh() {
        if (busy) return;
        busy = true;
        try {
            const response = await fetch('${ROOT}.css', {cache: 'no-store'});
            if (response.ok) {
                const css = await response.text();
                if (style.textContent !== css) style.textContent = css;
            }
        } catch (_) { /* Keep the last palette while offline. */ }
        finally { busy = false; }
    }
    refresh();
    setInterval(refresh, 2000);
})();`;

function install(cssPath) {
    const originalEmit = http.Server.prototype.emit;
    http.Server.prototype.emit = function (event, req, res, ...args) {
        if (event !== 'request') return originalEmit.call(this, event, req, res, ...args);
        if (req.method === 'GET' && [ROOT + '.css', ROOT + '.js'].includes(req.url)) {
            res.setHeader('Cache-Control', 'no-store');
            if (req.url.endsWith('.js')) {
                res.setHeader('Content-Type', 'application/javascript; charset=utf-8');
                res.end(client);
            } else {
                try {
                    res.setHeader('Content-Type', 'text/css; charset=utf-8');
                    res.end(fs.readFileSync(cssPath));
                } catch (_) { res.statusCode = 404; res.end(); }
            }
            return true;
        }
        // Only the official UI's initial HTML, never streams, addons, or other proxy URLs.
        if (req.method === 'GET' && req.url === '/proxy/d=https%3A%2F%2Fweb.stremio.com/') {
            delete req.headers['if-none-match'];
            delete req.headers['if-modified-since'];
            const head = res.writeHead, write = res.write, end = res.end;
            let chunks = [], length = 0;
            res.writeHead = function (status, reason, headers) {
                this.statusCode = status;
                if (typeof reason === 'string') this.statusMessage = reason;
                else headers = reason;
                if (Array.isArray(headers)) {
                    for (let i = 0; i < headers.length; i += 2) this.setHeader(headers[i], headers[i + 1]);
                } else for (const [name, value] of Object.entries(headers || {})) this.setHeader(name, value);
                return this;
            };
            const restore = () => { res.writeHead = head; res.write = write; res.end = end; };
            res.write = function (chunk, encoding, callback) {
                if (typeof encoding === 'function') { callback = encoding; encoding = undefined; }
                const data = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk, encoding);
                chunks.push(data); length += data.length;
                // Fail open on unexpectedly large responses instead of buffering indefinitely.
                if (length > 2 * 1024 * 1024) {
                    restore();
                    return write.call(this, Buffer.concat(chunks), callback);
                }
                if (callback) process.nextTick(callback);
                return true;
            };
            res.end = function (chunk, encoding, callback) {
                if (typeof chunk === 'function') { callback = chunk; chunk = undefined; }
                if (typeof encoding === 'function') { callback = encoding; encoding = undefined; }
                if (chunk) this.write(chunk, encoding);
                // write() may have switched back to streaming at the size limit.
                if (this.end === end) return end.call(this, callback);
                let body = Buffer.concat(chunks);
                try {
                    if (this.statusCode === 200 && String(this.getHeader('Content-Type')).includes('text/html')) {
                        const coding = String(this.getHeader('Content-Encoding') || '').toLowerCase();
                        const decode = {gzip: zlib.gunzipSync, deflate: zlib.inflateSync, br: zlib.brotliDecompressSync};
                        if (coding && !decode[coding]) throw new Error('Unknown content encoding');
                        const html = (coding ? decode[coding](body, {maxOutputLength: 2 * 1024 * 1024}) : body).toString();
                        if (html.includes('</head>') && !html.includes(MARKER)) {
                            body = Buffer.from(html.replace('</head>',
                                `<script ${MARKER} src="${ROOT}.js" defer></script></head>`));
                            for (const name of ['Content-Length', 'Content-Encoding', 'ETag', 'Last-Modified']) this.removeHeader(name);
                            this.setHeader('Cache-Control', 'no-store');
                        }
                    }
                } catch (_) { /* Preserve the upstream bytes and headers on failure. */ }
                restore();
                return end.call(this, body, callback);
            };
        }
        return originalEmit.call(this, event, req, res, ...args);
    };
}

// NODE_OPTIONS may also reach helper processes: only activate in the Stremio server.
if (process.env.BWM_STREMIO_CSS && /\/stremio\/server\.js$/.test(process.argv[1] || '')) {
    install(process.env.BWM_STREMIO_CSS);
}
module.exports = {install};
