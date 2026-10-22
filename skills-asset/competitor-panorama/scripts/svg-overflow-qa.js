#!/usr/bin/env node
/**
 * svg-overflow-qa.js — 检测 HTML 报告内联 SVG 中所有 <text> 是否越出 viewBox。
 *
 * transform 感知：用 getBoundingClientRect（含旋转等变换）映射回 viewBox 坐标，
 * 可正确检测 rotate(90) 竖排文字；getBBox 对带 transform 的 text 会报未旋转的
 * bbox（误报），所以不用。
 *
 * 依赖：Node.js + 本机 Chrome（无 npm 依赖）。
 * 用法：node svg-overflow-qa.js <报告.html> [chrome 可执行文件路径]
 * 退出码：0=无越界（含 0 个 text 的情况）  1=存在越界  2=参数错误/脚本未执行
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');

const args = process.argv.slice(2);
const isHelp = args.includes('-h') || args.includes('--help');
if (!args[0] || isHelp) {
  console.log('用法: node svg-overflow-qa.js <报告.html> [chrome可执行路径]');
  console.log('默认 Chrome: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
  console.log('退出码: 0=无越界 1=存在越界 2=参数错误或脚本未执行');
  process.exit(isHelp ? 0 : 2);
}

const filePath = path.resolve(args[0]);
const chrome = args[1] || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if (!fs.existsSync(filePath)) {
  console.error('文件不存在: ' + filePath);
  process.exit(2);
}

// 注入页面的测量脚本（注意：join 用 String.fromCharCode(10) 规避转义坑）
const injected = String.raw`<script>
(function(){
  function measure(){
    var out = [];
    try {
      var svgs = Array.prototype.slice.call(document.querySelectorAll("svg"));
      var texts = Array.prototype.slice.call(document.querySelectorAll("svg text"));
      var sr = svgs.map(function(sv){
        return { sv: sv, r: sv.getBoundingClientRect(), vb: sv.viewBox ? sv.viewBox.baseVal : null };
      });
      var overflow = 0;
      texts.forEach(function(t){
        var f = null;
        for (var i = 0; i < sr.length; i++) { if (sr[i].sv.contains(t)) { f = sr[i]; break; } }
        if (!f || !f.vb || f.vb.width === 0 || f.vb.height === 0 || f.r.width === 0 || f.r.height === 0) return;
        var b = t.getBoundingClientRect();
        var sx = f.vb.width / f.r.width;
        var sy = f.vb.height / f.r.height;
        var l = (b.left - f.r.left) * sx;
        var tp = (b.top - f.r.top) * sy;
        var w = b.width * sx;
        var h = b.height * sy;
        if (l < -1 || tp < -1 || l + w > f.vb.width + 1 || tp + h > f.vb.height + 1) {
          overflow++;
          var label = String(t.textContent).replace(/\s+/g, ' ').trim().slice(0, 30);
          out.push('OVERFLOW|' + (f.sv.id || '(no-id)') + '|' + label +
            '|left=' + l.toFixed(1) + ',top=' + tp.toFixed(1) + ',w=' + w.toFixed(1) + ',h=' + h.toFixed(1) +
            '|vb=' + f.vb.width + 'x' + f.vb.height);
        }
      });
      out.push('RESULT|texts=' + texts.length + '|overflow=' + overflow);
    } catch (e) { out.push('FATAL|' + e.message); }
    var pre = document.createElement('pre');
    pre.id = 'qa-result';
    pre.textContent = out.join(String.fromCharCode(10));
    document.body.appendChild(pre);
  }
  if (document.readyState === 'complete' || document.readyState === 'interactive') { measure(); }
  else { window.addEventListener('DOMContentLoaded', measure); }
})();
</script>`;

// 注入副本（兼容无 </body> 闭合的报告文件）
const html = fs.readFileSync(filePath, 'utf8');
let patched;
if (html.includes('</body>')) {
  patched = html.replace('</body>', injected + '\n</body>');
} else {
  const i = html.lastIndexOf('</html>');
  patched = i >= 0 ? html.slice(0, i) + injected + '\n' + html.slice(i) : html + injected;
}
const tmp = path.join(os.tmpdir(), 'svg-qa-' + process.pid + '-' + Date.now() + '.html');
fs.writeFileSync(tmp, patched);

try {
  const dom = execFileSync(
    chrome,
    ['--headless', '--disable-gpu', '--virtual-time-budget=8000', '--dump-dom', 'file://' + tmp],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 120000 }
  );
  const m = dom.match(/<pre id="qa-result">([\s\S]*?)<\/pre>/);
  if (!m) {
    console.error('测量脚本未执行：请确认 Chrome 可用且 HTML 可正常打开');
    process.exitCode = 2;
  } else {
    const lines = m[1].split('\n');
    lines.forEach(function (l) { console.log(l); });
    if (lines.some(function (l) { return l.indexOf('FATAL|') === 0; })) {
      process.exitCode = 2;
    } else if (lines.some(function (l) { return l.indexOf('OVERFLOW|') === 0; })) {
      console.log('\n存在越界文字，请修正坐标或缩短文案后重跑。');
      process.exitCode = 1;
    } else {
      console.log('\nPASS: 全部 SVG text 均在各自 viewBox 内。');
      process.exitCode = 0;
    }
  }
} finally {
  try { fs.unlinkSync(tmp); } catch (e) { /* 忽略清理失败 */ }
}