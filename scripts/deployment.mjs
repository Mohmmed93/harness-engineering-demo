import { writeFile } from 'node:fs/promises';

const mode = process.argv[2];
const sha = process.env.GITHUB_SHA || process.env.EXPECTED_SHA;
if (!sha || !/^[a-f0-9]{40}$/.test(sha)) throw new Error('A full commit SHA is required');

if (mode === 'stamp') {
  await writeFile('dist/deployment.json', JSON.stringify({ sha }) + '\n');
} else if (mode === 'check') {
  const base = process.env.SMOKE_BASE_URL;
  if (!base) throw new Error('SMOKE_BASE_URL is required');
  const url = new URL('deployment.json', base.endsWith('/') ? base : `${base}/`);
  let verified = false;
  for (let attempt = 1; attempt <= 12; attempt++) {
    try {
      url.searchParams.set('run', `${sha}-${attempt}-${Date.now()}`);
      const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(5000) });
      if (response.ok && (await response.json()).sha === sha) {
        console.log(`Verified deployed commit ${sha}`);
        verified = true;
        break;
      }
    } catch { /* A newly published Pages artifact can take a moment to appear. */ }
    console.log(`Deployment is not ready at the expected commit (attempt ${attempt}/12)`);
    if (attempt < 12) await new Promise(resolve => setTimeout(resolve, 5000));
  }
  if (!verified) throw new Error('Could not verify deployed commit; smoke results must not be attributed to this SHA');
} else {
  throw new Error('Use stamp or check');
}
