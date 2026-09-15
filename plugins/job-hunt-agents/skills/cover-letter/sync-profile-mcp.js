#!/usr/bin/env node
/**
 * Automatically fetch LinkedIn profile sections via mcp-chrome without any manual copy-pasting or PDF printing.
 *
 * Usage:
 *   node sync-profile-mcp.js <handle-or-url> [--dest /path/to/profile]
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SECTIONS = [
  { name: 'profile', pathSuffix: '' },
  { name: 'experience', pathSuffix: 'details/experience/' },
  { name: 'projects', pathSuffix: 'details/projects/' },
  { name: 'certifications', pathSuffix: 'details/certifications/' },
  { name: 'skills', pathSuffix: 'details/skills/' },
];

function resolveWorkspace() {
  if (process.env.JOB_HUNT_HOME) {
    return path.resolve(process.env.JOB_HUNT_HOME);
  }
  const root = path.resolve(__dirname, '../..');
  try {
    const ws = execSync(`python3 "${path.join(root, 'bin/workspace-path.py')}"`, { encoding: 'utf-8' }).trim().split('\n').pop();
    if (ws) return ws;
  } catch (e) {}
  return path.join(process.env.HOME || '', 'Documents/job_applications');
}

function getBridgePath() {
  const custom = process.env.MCP_CHROME_BRIDGE;
  if (custom && fs.existsSync(custom)) return custom;
  try {
    const npmRoot = execSync('npm root -g', { encoding: 'utf-8' }).trim();
    const candidate = path.join(npmRoot, 'mcp-chrome-bridge/dist/mcp/mcp-server-stdio.js');
    if (fs.existsSync(candidate)) return candidate;
  } catch (e) {}
  const macDefault = '/opt/homebrew/lib/node_modules/mcp-chrome-bridge/dist/mcp/mcp-server-stdio.js';
  if (fs.existsSync(macDefault)) return macDefault;
  throw new Error('mcp-chrome-bridge not found. Install it with: npm install -g mcp-chrome-bridge');
}

function parseHandle(input) {
  let handle = input.trim();
  const m = handle.match(/linkedin\.com\/in\/([^\/\?#]+)/);
  if (m) handle = m[1];
  return handle.replace(/[\/\?#].*$/, '');
}

class McpClient {
  constructor(bridgePath) {
    this.proc = spawn('node', [bridgePath], { stdio: ['pipe', 'pipe', 'inherit'] });
    this.reqId = 1;
    this.pending = new Map();
    this.buffer = '';

    this.proc.stdout.on('data', (chunk) => {
      this.buffer += chunk.toString();
      const lines = this.buffer.split('\n');
      this.buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.id && this.pending.has(msg.id)) {
            const { resolve, reject } = this.pending.get(msg.id);
            this.pending.delete(msg.id);
            if (msg.error) reject(new Error(msg.error.message || JSON.stringify(msg.error)));
            else resolve(msg.result);
          }
        } catch (err) {
          // ignore non-json
        }
      }
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.reqId++;
      this.pending.set(id, { resolve, reject });
      const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n';
      this.proc.stdin.write(payload);
    });
  }

  async init() {
    await this.send('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'sync-profile-mcp', version: '1.0' },
    });
  }

  async callTool(name, args = {}) {
    const res = await this.send('tools/call', { name, arguments: args });
    return res;
  }

  close() {
    try {
      this.proc.stdin.end();
      this.proc.kill();
    } catch (e) {}
  }
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const args = process.argv.slice(2);
  if (!args[0]) {
    console.error('Usage: node sync-profile-mcp.js <linkedin-handle-or-url> [--dest /path/to/profile]');
    process.exit(1);
  }

  const handle = parseHandle(args[0]);
  let destDir = '';
  const destIdx = args.indexOf('--dest');
  if (destIdx !== -1 && args[destIdx + 1]) {
    destDir = path.resolve(args[destIdx + 1]);
  } else {
    destDir = path.join(resolveWorkspace(), 'profile');
  }

  const outDir = path.join(destDir, '.text');
  fs.mkdirSync(outDir, { recursive: true });

  console.log(`[mcp-chrome] Syncing LinkedIn profile for: ${handle}`);
  console.log(`[mcp-chrome] Target output: ${outDir}`);

  const bridgePath = getBridgePath();
  const client = new McpClient(bridgePath);
  await client.init();

  let activeTabId = null;

  try {
    for (const section of SECTIONS) {
      const targetUrl = `https://www.linkedin.com/in/${handle}/${section.pathSuffix}`;
      process.stdout.write(`[mcp-chrome] Reading ${section.name} (${targetUrl})... `);

      let text = '';
      if (!activeTabId) {
        // First navigation
        const navRes = await client.callTool('chrome_navigate', { url: targetUrl });
        const resText = navRes.content?.[0]?.text || '';
        const match = resText.match(/"tabId":\s*(\d+)/);
        if (match) activeTabId = Number(match[1]);
      } else {
        await client.callTool('chrome_navigate', { tabId: activeTabId, url: targetUrl });
      }

      // Wait a moment for dynamic page render
      await sleep(2500);

      // Extract web content
      const contentRes = await client.callTool('chrome_get_web_content', {
        tabId: activeTabId,
        textContent: true,
      });

      const jsonContent = contentRes.content?.[0]?.text || '';
      try {
        const parsed = JSON.parse(jsonContent);
        text = parsed.textContent || '';
      } catch (e) {
        text = jsonContent;
      }

      text = text.replace(/\n{3,}/g, '\n\n').trim();
      const targetFile = path.join(outDir, `${section.name}.txt`);
      fs.writeFileSync(targetFile, text + '\n', 'utf-8');
      console.log(`✓ (${text.length} chars) -> ${section.name}.txt`);
    }

    // Close the tab we opened
    if (activeTabId) {
      try {
        await client.callTool('chrome_close_tabs', { tabIds: [activeTabId] });
      } catch (e) {}
    }

    console.log(`\n[mcp-chrome] All 5 sections saved successfully in: ${outDir}`);
  } finally {
    client.close();
  }
}

main().catch((err) => {
  console.error('[mcp-chrome] ERROR:', err.message);
  process.exit(1);
});
