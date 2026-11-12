// Falha se encontrar caracteres CJK (fora de comentários) em src/**/*.{ts,tsx,json}.
// Uso: node scripts/check-no-cjk.mjs [caminhos...]
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(import.meta.url), '..', '..');
const EXTS = new Set(['.ts', '.tsx', '.json']);
const CJK = /[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef]/;

function walk(path, out) {
  const st = statSync(path);
  if (st.isDirectory()) {
    for (const name of readdirSync(path)) {
      if (name === 'node_modules') continue;
      walk(join(path, name), out);
    }
  } else if (EXTS.has(extname(path))) {
    out.push(path);
  }
}

// Remove comentários // e /* */ preservando quebras de linha e strings.
function stripComments(src, isJson) {
  if (isJson) return src;
  let out = '';
  let i = 0;
  const n = src.length;
  while (i < n) {
    const c = src[i];
    const d = src[i + 1];
    if (c === '"' || c === "'" || c === '`') {
      let j = i + 1;
      while (j < n && src[j] !== c) {
        if (src[j] === '\\') j++;
        j++;
      }
      out += src.slice(i, j + 1);
      i = j + 1;
    } else if (c === '/' && d === '/') {
      while (i < n && src[i] !== '\n') i++;
    } else if (c === '/' && d === '*') {
      const end = src.indexOf('*/', i + 2);
      const stop = end === -1 ? n : end + 2;
      out += src.slice(i, stop).replace(/[^\n]/g, '');
      i = stop;
    } else {
      out += c;
      i++;
    }
  }
  return out;
}

const args = process.argv.slice(2);
const targets = args.length ? args.map((a) => resolve(process.cwd(), a)) : [join(root, 'src')];
const files = [];
for (const t of targets) {
  try {
    walk(t, files);
  } catch {
    console.error(`caminho não encontrado: ${t}`);
    process.exit(2);
  }
}

let found = 0;
for (const file of files.sort()) {
  const raw = readFileSync(file, 'utf8');
  const lines = stripComments(raw, extname(file) === '.json').split('\n');
  const rawLines = raw.split('\n');
  lines.forEach((line, idx) => {
    if (CJK.test(line)) {
      found++;
      const rel = file.startsWith(root) ? file.slice(root.length + 1) : file;
      console.log(`${rel}:${idx + 1}: ${rawLines[idx].trim().slice(0, 120)}`);
    }
  });
}
if (found) {
  console.error(`\n${found} linha(s) com caracteres CJK.`);
  process.exit(1);
}
