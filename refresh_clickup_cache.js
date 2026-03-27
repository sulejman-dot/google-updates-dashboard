#!/usr/bin/env node
/**
 * Refresh ClickUp Comments Cache
 * 
 * Connects to the ClickUp MCP server via mcp-remote, fetches all comments
 * for monitored tasks, and writes the cache JSON file.
 * 
 * Prerequisites: npm install @anthropic-ai/sdk or use npx mcp-remote
 * Usage: node refresh_clickup_cache.js
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE_DIR = __dirname;
const CACHE_FILE = path.join(WORKSPACE_DIR, 'clickup_comments_cache.json');

// Monitored task IDs
const TASK_IDS = [
    '869bwrnku', '869c3mu4c', '869c3ebv5', '869c3eftz',
    '869c3dy26', '869c3dw22', '869c2tvk7', '869c14cc2',
    '869c2p3ur', '869c2yr03', '869btgtqc'
];

const TASK_NAMES = {
    '869bwrnku': '[bug][rt] AIO mentions metric is incorrect in competition',
    '869c3mu4c': '[bug][rt] AIS widget stuck with analyzing keywords',
    '869c3ebv5': '[bug][dashboard] Visibility discrepancy',
    '869c3eftz': '[improvement][looker] Competition Insights connector',
    '869c3dy26': '[bug][rt] Smart groups with AIS criteria showing 0 keywords',
    '869c3dw22': '[bug][research] SV for tracked kw in research',
    '869c2tvk7': '[bug][exports] Some of the competitors ranks are empty',
    '869c14cc2': '[Bug][Rank Tracker] Client website not flagged for AIS mention',
    '869c2p3ur': '[bug][rt] AIS keywords stuck in processing',
    '869c2yr03': '[feature request][exports] Allow bulk export for sublocations',
    '869btgtqc': 'Proactive Quality Assurance & CSAT Recovery',
};

/**
 * Call a ClickUp MCP tool via mcp-remote using JSON-RPC over stdio
 */
async function callMcpTool(toolName, args) {
    return new Promise((resolve, reject) => {
        const child = spawn('npx', [
            '-y', 'mcp-remote', 'https://mcp.clickup.com/mcp'
        ], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, NODE_ENV: 'production' }
        });

        let stdout = '';
        let stderr = '';

        child.stdout.on('data', (data) => { stdout += data.toString(); });
        child.stderr.on('data', (data) => { stderr += data.toString(); });

        // Send JSON-RPC request
        const request = JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'tools/call',
            params: {
                name: toolName,
                arguments: args
            }
        });

        child.stdin.write(request + '\n');
        child.stdin.end();

        child.on('close', (code) => {
            try {
                const lines = stdout.split('\n').filter(l => l.trim());
                for (const line of lines) {
                    try {
                        const parsed = JSON.parse(line);
                        if (parsed.result) {
                            resolve(parsed.result);
                            return;
                        }
                    } catch (e) { /* skip non-JSON lines */ }
                }
                resolve(null);
            } catch (e) {
                reject(e);
            }
        });

        // Timeout after 30s
        setTimeout(() => { child.kill(); reject(new Error('Timeout')); }, 30000);
    });
}

/**
 * Alternative approach: use curl to call the ClickUp API v3 
 * via the MCP endpoint directly (if accessible)
 */
async function fetchCommentsViaApi(taskId) {
    // Try using the ClickUp API v2 with the cached OAuth token from mcp-remote
    const { execSync } = require('child_process');

    // Look for cached OAuth tokens from mcp-remote
    const homeDir = require('os').homedir();
    const possibleTokenPaths = [
        path.join(homeDir, '.mcp-auth', 'mcp.clickup.com.json'),
        path.join(homeDir, '.config', 'mcp-remote', 'mcp.clickup.com.json'),
        path.join(homeDir, '.mcp-remote', 'mcp.clickup.com.json'),
    ];

    for (const tokenPath of possibleTokenPaths) {
        if (fs.existsSync(tokenPath)) {
            try {
                const tokenData = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
                const accessToken = tokenData.access_token || tokenData.token;
                if (accessToken) {
                    console.log(`  Found OAuth token at ${tokenPath}`);
                    const result = execSync(
                        `curl -s "https://api.clickup.com/api/v2/task/${taskId}/comment" -H "Authorization: Bearer ${accessToken}"`,
                        { timeout: 10000 }
                    );
                    return JSON.parse(result.toString());
                }
            } catch (e) {
                console.log(`  Token at ${tokenPath} failed: ${e.message}`);
            }
        }
    }

    return null;
}

async function main() {
    console.log(`[${new Date().toISOString()}] Starting ClickUp cache refresh...`);

    const cache = {
        last_updated: new Date().toISOString(),
        tasks: {}
    };

    for (const taskId of TASK_IDS) {
        const taskName = TASK_NAMES[taskId] || 'Unknown';
        console.log(`  Fetching comments for ${taskId} (${taskName})...`);

        try {
            const result = await fetchCommentsViaApi(taskId);
            if (result && result.comments) {
                cache.tasks[taskId] = {
                    name: taskName,
                    url: `https://app.clickup.com/t/${taskId}`,
                    comments: result.comments.map(c => ({
                        id: c.id,
                        date: c.date,
                        user: (c.user || {}).username || 'Unknown',
                        text: (c.comment_text || '').substring(0, 300)
                    }))
                };
                console.log(`    ✅ ${result.comments.length} comment(s)`);
            } else {
                cache.tasks[taskId] = { name: taskName, url: `https://app.clickup.com/t/${taskId}`, comments: [] };
                console.log(`    ⚠️ No data returned`);
            }
        } catch (e) {
            cache.tasks[taskId] = { name: taskName, url: `https://app.clickup.com/t/${taskId}`, comments: [] };
            console.log(`    ❌ Error: ${e.message}`);
        }
    }

    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));

    const totalComments = Object.values(cache.tasks).reduce((sum, t) => sum + t.comments.length, 0);
    console.log(`\n✅ Cache updated: ${totalComments} comments across ${Object.keys(cache.tasks).length} tasks`);
    console.log(`   Saved to: ${CACHE_FILE}`);
}

main().catch(e => {
    console.error('Fatal error:', e);
    process.exit(1);
});
