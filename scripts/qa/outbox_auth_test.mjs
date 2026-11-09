// /api/outbox/* — who may read and change the publishing queue (docs/RUNBOOK.md 3.39). The real worker/_worker.js is
// imported in Node; a throw-away RSA key plays GitHub's OIDC key. Checks that only a valid token of the workflow
// outbox.yml on the default branch of hemptoon/blokvolt-rs or hemptoon/evolako-web, for the audience outbox.blokvolt.rs,
// passes — and that a wrong signature, audience, issuer, repository, workflow, branch or an expired token do not.
// Usage: node --no-warnings scripts/qa/outbox_auth_test.mjs
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

globalThis.OUTBOX_TEST = {};
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
await import(pathToFileURL(path.join(REPO, 'worker', '_worker.js')).href);
const auth = globalThis.OUTBOX_TEST.auth;

let fails = 0, oks = 0;
const check = (cond, what) => { if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what); } };

const alg = { name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' };
const good = await crypto.subtle.generateKey(alg, true, ['sign', 'verify']);
const evil = await crypto.subtle.generateKey(alg, true, ['sign', 'verify']);
const jwk = { ...(await crypto.subtle.exportKey('jwk', good.publicKey)), kid: 'k1' };
const keys = async () => [jwk];

const b64u = b => Buffer.from(b).toString('base64url');
const NOW = 1_800_000_000;
async function token(over = {}, { key = good.privateKey, head = {} } = {}) {
  const h = { alg: 'RS256', kid: 'k1', typ: 'JWT', ...head };
  const c = {
    iss: 'https://token.actions.githubusercontent.com', aud: 'outbox.blokvolt.rs', exp: NOW + 300, nbf: NOW - 10,
    repository: 'hemptoon/blokvolt-rs', ref: 'refs/heads/main',
    job_workflow_ref: 'hemptoon/blokvolt-rs/.github/workflows/outbox.yml@refs/heads/main', ...over,
  };
  const data = b64u(JSON.stringify(h)) + '.' + b64u(JSON.stringify(c));
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(data));
  return data + '.' + b64u(new Uint8Array(sig));
}
const req = t => new Request('https://www.blokvolt.rs/api/outbox/next', { method: 'POST', headers: t ? { authorization: 'Bearer ' + t } : {} });
const run = async t => auth(req(t), keys, NOW);

check((await run(await token()))?.repository === 'hemptoon/blokvolt-rs', 'blokvolt-rs, outbox.yml on main: accepted');
check((await run(await token({ repository: 'hemptoon/evolako-web', job_workflow_ref: 'hemptoon/evolako-web/.github/workflows/outbox.yml@refs/heads/main' })))?.repository === 'hemptoon/evolako-web', 'evolako-web, outbox.yml on main: accepted');
check(await run(null) === null, 'no token: refused');
check(await run('abc.def.ghi') === null, 'garbage: refused');
check(await run(await token({}, { key: evil.privateKey })) === null, 'signed with another key: refused');
check(await run(await token({}, { head: { kid: 'other' } })) === null, 'unknown key id: refused');
check(await run(await token({}, { head: { alg: 'none' } })) === null, 'alg none: refused');
check(await run(await token({ aud: 'something-else' })) === null, 'wrong audience: refused');
check(await run(await token({ iss: 'https://evil.example' })) === null, 'wrong issuer: refused');
check(await run(await token({ exp: NOW - 1 })) === null, 'expired: refused');
check(await run(await token({ repository: 'someone/fork', job_workflow_ref: 'someone/fork/.github/workflows/outbox.yml@refs/heads/main' })) === null, 'other repository: refused');
check(await run(await token({ job_workflow_ref: 'hemptoon/blokvolt-rs/.github/workflows/deploy.yml@refs/heads/main' })) === null, 'other workflow: refused');
check(await run(await token({ ref: 'refs/heads/feature', job_workflow_ref: 'hemptoon/blokvolt-rs/.github/workflows/outbox.yml@refs/heads/feature' })) === null, 'workflow on another branch: refused');
check(await run(await token({ ref: 'refs/pull/1/merge' })) === null, 'pull request ref: refused');

console.log(`\n${oks} ok, ${fails} failed`);
process.exit(fails ? 1 : 0);
