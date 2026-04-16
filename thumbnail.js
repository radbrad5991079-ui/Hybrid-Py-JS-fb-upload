const puppeteer = require('puppeteer');
const { execSync } = require('child_process');
const fs = require('fs');

// Python se Title aur Output Path receive karna
const titleText = process.argv[2] || "LIVE MATCH";
const outputImagePath = process.argv[3] || "thumbnail.png";

async function generateThumbnail() {
    console.log(`\n[🎨 JS] Puppeteer se HD Thumbnail bana raha hoon...`);
    
    if (!fs.existsSync('data.json')) {
        console.log(`  [❌ JS] 'data.json' nahi mili!`);
        process.exit(1);
    }

    const data = JSON.parse(fs.readFileSync('data.json', 'utf8'));
    const rawFrame = 'temp_raw_frame.jpg';
    
    try {
        const headersCmd = `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: ${data.referer}\r\nCookie: ${data.cookie}\r\n`;
        execSync(`ffmpeg -y -headers "${headersCmd}" -i "${data.url}" -vframes 1 -q:v 2 ${rawFrame}`, { stdio: 'ignore' });
    } catch (e) { 
        console.log(`  [❌ JS] FFmpeg frame extract nahi kar saka.`);
        process.exit(1);
    }

    if (!fs.existsSync(rawFrame)) process.exit(1);
    const b64Image = "data:image/jpeg;base64," + fs.readFileSync(rawFrame).toString('base64');
    
    const htmlCode = `
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@700;900&display=swap" rel="stylesheet">
        <style>
            body { margin: 0; width: 1280px; height: 720px; background: #0f0f0f; font-family: 'Roboto', sans-serif; color: white; display: flex; flex-direction: column; overflow: hidden; }
            .header { height: 100px; display: flex; align-items: center; padding: 0 40px; justify-content: space-between; z-index: 10; }
            .logo { font-size: 50px; font-weight: 900; letter-spacing: 1px; text-shadow: 0 0 10px rgba(255,255,255,0.8); }
            .live-badge { border: 4px solid #cc0000; border-radius: 12px; padding: 5px 20px; font-size: 40px; font-weight: 700; display: flex; gap: 10px; }
            .hero-container { position: relative; width: 100%; height: 440px; }
            .hero-img { width: 100%; height: 100%; object-fit: cover; filter: blur(5px); opacity: 0.6; }
            .pip-img { position: absolute; top: 20px; right: 40px; width: 45%; border: 6px solid white; box-shadow: -15px 15px 30px rgba(0,0,0,0.8); }
            .text-container { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 10px 40px; }
            .main-title { font-size: 70px; font-weight: 900; line-height: 1.1; text-shadow: 6px 6px 15px rgba(0,0,0,0.9); }
            .live-text { color: #cc0000; }
        </style>
        </head><body>
            <div class="header"><div class="logo">SPORTSHUB</div><div class="live-badge"><span style="color:#cc0000">●</span> LIVE</div></div>
            <div class="hero-container"><img src="${b64Image}" class="hero-img"><img src="${b64Image}" class="pip-img"></div>
            <div class="text-container"><div class="main-title"><span class="live-text">LIVE NOW: </span>${titleText}</div></div>
        </body></html>`;

    const browser = await puppeteer.launch({ headless: true, defaultViewport: { width: 1280, height: 720 }, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.setContent(htmlCode);
    await page.screenshot({ path: outputImagePath });
    await browser.close();
    
    if (fs.existsSync(rawFrame)) fs.unlinkSync(rawFrame); 
    console.log(`  [✅ JS] Thumbnail Ready: ${outputImagePath}`);
}

generateThumbnail();
