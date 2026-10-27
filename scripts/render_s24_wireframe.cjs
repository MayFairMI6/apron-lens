// Wrap verified Unity screen renders in an illustrative phone shell; no app pixels redrawn.
const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const out=path.join(root,'outputs/milestone1/s24');
const config=[['Now','s24-now.png'],['Qwen','s24-qwen.png'],['History','s24-history.png']];
async function run(){
 const cards=config.map(([title,file])=>{
  const png=fs.readFileSync(path.join(out,file)).toString('base64');
  return `<section><h2>${title}</h2><div class="phone"><img src="data:image/png;base64,${png}" alt="Actual Unity ${title} screen at Galaxy S24 resolution"><div class="hole"></div><div class="gesture"></div></div></section>`;
 }).join('');
 const html=`<!doctype html><meta charset="utf-8"><title>Galaxy S24 · UI layout test</title><style>
 *{box-sizing:border-box}body{margin:0;padding:30px 34px;background:#edf1f3;color:#142530;font-family:Arial,sans-serif}h1{font-size:27px;margin:0 0 8px}p{font-size:14px;color:#4b616e;margin:0 0 18px}main{display:flex;gap:32px}section{width:310px}h2{font-size:17px;font-weight:600;margin:0 0 12px}.phone{position:relative;padding:7px;background:#15232d;border:2px solid #72838c;border-radius:31px;box-shadow:0 10px 22px #14253018}.phone img{display:block;width:292px;height:632.667px;border-radius:23px}.hole{position:absolute;top:12px;left:calc(50% - 4px);width:8px;height:8px;background:#0b1318;border-radius:50%}.gesture{position:absolute;bottom:14px;left:calc(50% - 35px);width:70px;height:3px;background:#b7c0c6;border-radius:3px}footer{font-size:13px;color:#4b616e;margin-top:22px;max-width:960px;line-height:1.5}a{color:#00686c}
 </style><h1>Galaxy S24 · Smartphone layout test</h1><p>1080 × 2340 portrait · actual Unity UI renders inside an illustrative device outline</p><main>${cards}</main><footer>Simulated safe areas: 90 px above and 72 px below. Camera hole and outer frame are illustrative. This tests layout; it does not establish Android runtime, camera tracking or physical touch behavior. <a href="https://www.samsung.com/sa_en/business/smartphones/galaxy-s/galaxy-s24-onyx-black-128gb-sm-s921bzkbmea/">Samsung display specification</a></footer>`;
 const file=path.join(out,'s24-wireframe.html');fs.writeFileSync(file,html);
 const browser=await chromium.launch({headless:true,...(process.env.AIRFIELD_CHROMIUM ? {executablePath:process.env.AIRFIELD_CHROMIUM} : {})});
 const page=await browser.newPage({viewport:{width:1070,height:850},deviceScaleFactor:1});
 await page.goto('file://'+file);await page.screenshot({path:path.join(out,'s24-wireframe.png'),fullPage:true});
 await browser.close();console.log('Created S24 wireframe from actual screen renders.');
}
run().catch(e=>{console.error(e.message);process.exit(1)});
