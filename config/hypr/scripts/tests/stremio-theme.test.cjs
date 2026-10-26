'use strict';
const {test, after} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');
const {install} = require('../stremio-theme.cjs');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'bwm-stremio-test-'));
const css = path.join(directory, 'theme.css');
const originalEmit = http.Server.prototype.emit;
install(css);
after(() => { http.Server.prototype.emit = originalEmit; fs.rmSync(directory, {recursive: true}); });
const route = '/proxy/d=https%3A%2F%2Fweb.stremio.com/';

async function request(handler, url = route, method = 'GET') {
    const server = http.createServer(handler);
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    try {
        return await new Promise((resolve, reject) => {
            http.request({host: '127.0.0.1', port: server.address().port, path: url, method}, res => {
                const chunks = [];
                res.on('data', chunk => chunks.push(chunk));
                res.on('end', () => resolve({status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks)}));
            }).on('error', reject).end();
        });
    } finally { await new Promise(resolve => server.close(resolve)); }
}

for (const encoding of ['', 'gzip', 'br', 'deflate']) {
    test(`inject UI HTML, preserving content (${encoding || 'identity'})`, async () => {
        const html = '<html><head><title>Stremio</title></head><body>original</body></html>';
        const encoders = {gzip: zlib.gzipSync, br: zlib.brotliCompressSync, deflate: zlib.deflateSync};
        const data = encoding ? encoders[encoding](Buffer.from(html)) : Buffer.from(html);
        const response = await request((req, res) => {
            res.writeHead(200, {'Content-Type': 'text/html', 'Content-Length': data.length,
                ...(encoding ? {'Content-Encoding': encoding} : {})});
            res.write(data.subarray(0, 12)); res.end(data.subarray(12));
        });
        assert.match(response.body.toString(), /data-bwm-theme/);
        assert.match(response.body.toString(), /<body>original<\/body>/);
        assert.equal(response.headers['content-encoding'], undefined);
        assert.equal(response.headers['cache-control'], 'no-store');
    });
}

test('media, API responses, and other proxied HTML are untouched', async () => {
    for (const url of ['/video/123', '/settings', '/proxy/d=https%3A%2F%2Fexample.com/']) {
        const body = Buffer.from('<html><head></head><body>unchanged</body></html>');
        const result = await request((req, res) => {
            res.writeHead(200, {'Content-Type': 'text/html', 'Content-Length': body.length});
            res.end(body);
        }, url);
        assert.deepEqual(result.body, body);
        assert.equal(Number(result.headers['content-length']), body.length);
    }
});

test('missing CSS fails safely and palette changes are served without restarting', async () => {
    const handler = () => assert.fail('BWM routes must not reach Stremio');
    assert.equal((await request(handler, '/__bwm_theme.css')).status, 404);
    for (const colour of ['#ff0000', '#00ff00']) {
        fs.writeFileSync(css, `:root {--primary-accent-color: ${colour}}`);
        assert.match((await request(handler, '/__bwm_theme.css')).body.toString(), new RegExp(colour));
    }
    assert.match((await request(handler, '/__bwm_theme.js')).body.toString(), /setInterval/);
});

test('unexpected or oversized upstream responses pass through unchanged', async () => {
    for (const [body, headers, status] of [
        [Buffer.from('broken gzip'), {'Content-Type': 'text/html', 'Content-Encoding': 'gzip'}, 200],
        [Buffer.from('<head></head>'), {'Content-Type': 'text/html'}, 500],
        [Buffer.from('{}'), {'Content-Type': 'application/json'}, 200],
        [Buffer.alloc(3 * 1024 * 1024, 65), {'Content-Type': 'text/html'}, 200],
    ]) {
        const result = await request((req, res) => {
            res.writeHead(status, {...headers, 'Content-Length': body.length}); res.end(body);
        });
        assert.deepEqual(result.body, body);
        assert.equal(result.status, status);
        assert.equal(result.headers['content-encoding'], headers['Content-Encoding']);
    }
});
