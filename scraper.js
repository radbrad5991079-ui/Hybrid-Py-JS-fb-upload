const puppeteer = require('puppeteer');
const fs = require('fs');

// ⚙️ SETTINGS & PROXY
const TARGET_URL = process.env.TARGET_URL || 'https://dadocric.st/player.php?id=ptvsp'; 

const USE_PROXY = process.env.USE_PROXY || 'No (Proxy OFF)';
const IS_PROXY_ON = USE_PROXY === 'Yes (Proxy ON)';

const PROXY_IP = process.env.PROXY_IP || '';
const PROXY_PORT = process.env.PROXY_PORT || '';
const PROXY_USER = process.env.PROXY_USER || '';
const PROXY_PASS = process.env.PROXY_PASS || '';

async function getStreamData() {
    console.log(`\n[🔍 JS] Puppeteer Chrome Start kar raha hoon...`);
    let browserArgs = ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled', '--mute-audio'];
    
    // 🛡️ PROXY LOGIC
    if (IS_PROXY_ON && PROXY_IP && PROXY_PORT) {
        browserArgs.push(`--proxy-server=http://${PROXY_IP}:${PROXY_PORT}`);
        console.log(`  [🛡️ JS] Proxy Mode: ON (${PROXY_IP})`);
    } else {
        console.log(`  [🚀 JS] Proxy Mode: OFF (Direct Connection)`);
    }

    const browser = await puppeteer.launch({ headless: true, args: browserArgs });
    const page = await browser.newPage();

    if (IS_PROXY_ON && PROXY_USER && PROXY_PASS) {
        await page.authenticate({ username: PROXY_USER, password: PROXY_PASS });
    }

    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

    let streamData = null;

    page.on('request', (request) => {
        const url = request.url();
        if (url.includes('.m3u8')) {
            const urlObj = new URL(url);
            const expires = urlObj.searchParams.get('expires') || urlObj.searchParams.get('e') || urlObj.searchParams.get('exp');
            let expireMs = expires ? parseInt(expires) * 1000 : Date.now() + (60 * 60 * 1000);

            streamData = {
                url: url,
                referer: request.headers()['referer'] || TARGET_URL,
                cookie: request.headers()['cookie'] || '',
                expireTime: expireMs
            };
        }
    });

    try {
        console.log(`  [🌐 JS] Target URL par ja raha hoon...`);
        await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 60000 });
        await page.click('body').catch(() => {});
        
        for (let i = 1; i <= 3; i++) {
            await new Promise(r => setTimeout(r, 5000));
            if (streamData) break;
        }
    } catch (e) {
        console.log(`  [❌ JS] Page load error.`);
    }
    
    await browser.close();

    if (streamData) {
        fs.writeFileSync('data.json', JSON.stringify(streamData, null, 2));
        console.log(`  [✅ JS] M3U8 Link 'data.json' mein save ho gaya!`);
        process.exit(0);
    } else {
        console.log(`  [🚨 JS] M3U8 Link nahi mila!`);
        process.exit(1); 
    }
}

getStreamData();
