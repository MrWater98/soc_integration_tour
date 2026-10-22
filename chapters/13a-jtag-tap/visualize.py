"""Offline visualization of actual simulation trace; no browser dependencies."""
import csv,json
from pathlib import Path

HTML = r'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>JTAG 引脚实验</title>
<style>body{max-width:1050px;margin:30px auto;padding:0 18px;font:17px system-ui;background:#f4f7fa;color:#183047}section{background:white;padding:20px;margin:15px 0;border-radius:12px}input{width:100%}canvas{width:100%;height:260px}pre{white-space:pre-wrap}button{padding:8px 18px;margin-right:10px}table{border-collapse:collapse}td,th{padding:7px 16px;border:1px solid #ddd}.high{color:#047857}.low{color:#64748b}</style>
<h1>JTAG：命令怎样变成引脚变化？</h1><p id="note"></p>
<section><button id="prev">上一事件</button><button id="next">下一事件</button><input id="range" type="range" min="0" value="0"><strong id="where"></strong><canvas id="wave" width="1000" height="260"></canvas></section>
<section><h2>这一刻的硬件</h2><pre id="route"></pre><table id="pins"></table><p id="action"></p></section>
<p>曲线来自 CSV。横轴是事件序号；不能据此推算真实板卡 JTAG 速度。更精确的仿真时间关系请打开 VCD。</p>
<script>
const rows=__ROWS__, perCycle=__CYCLE__;
const states=['RESET','IDLE','SELECT_DR','CAPTURE_DR','SHIFT_DR','EXIT1_DR','PAUSE_DR','EXIT2_DR','UPDATE_DR','SELECT_IR','CAPTURE_IR','SHIFT_IR','EXIT1_IR','PAUSE_IR','EXIT2_IR','UPDATE_IR'];
const slider=document.getElementById('range');slider.max=rows.length-1;
const state=v=>isNaN(Number(v))?v:states[Number(v)];
function show(){const n=Number(slider.value),r=rows[n];document.getElementById('where').textContent=`事件 ${n} / ${rows.length-1}`;
 document.getElementById('note').textContent=perCycle?'本图每行代表一个 TCK 周期，TCK 波形为示意重建。TDO 是上升沿前采样值。':'本图每行代表模拟适配器的一次引脚电平设置，直接对应实际 RTL 响应。';
 const before=r.pre?state(r.pre):null,after=state(r.post??r.state);
 const phase=before||after;
 document.getElementById('route').textContent=`外部测试器 -- TCK/TMS/TDI --> TAP [${before?before+' → ':''}${after}] -- TDO --> 测试器`+(r.ir!==undefined?`\n当前 IR=${r.ir}；USER=0x${Number(r.user).toString(16).padStart(8,'0')}`:'');
 let fields=['tck','tms','tdi','tdo','trst_n','fault','pin_out','pin_in'].filter(k=>r[k]!==undefined&&r[k]!=='');
 document.getElementById('pins').innerHTML='<tr><th>信号</th><th>值</th></tr>'+fields.map(k=>'<tr><td>'+k+'</td><td>'+(['pin_out','pin_in'].includes(k)?Number(r[k]).toString(2).padStart(4,'0'):r[k])+'</td></tr>').join('');
 document.getElementById('action').textContent=phase.includes('CAPTURE')?'Capture：把当前并行值复制到传输寄存器。':phase.includes('SHIFT')?'Shift：TDI 送入一位，TDO 送出一位；正式输出锁存器保持不变。':phase.includes('UPDATE')?'Update：按所选指令提交完整值。':phase==='RESET'?'TAP 复位状态；不等同于 CPU 或整颗 SoC 复位。':'TMS 控制接下来走哪条状态路径。';
 const ctx=document.getElementById('wave').getContext('2d');ctx.clearRect(0,0,1000,260);const keys=['tck','tms','tdi','tdo'];const start=Math.max(0,n-12),end=Math.min(rows.length,start+25),step=880/(end-start);
 keys.forEach((key,j)=>{const base=55+j*53;ctx.fillStyle='#183047';ctx.font='16px monospace';ctx.fillText(key.toUpperCase(),10,base);ctx.strokeStyle=['#2563eb','#7c3aed','#059669','#d97706'][j];ctx.lineWidth=2;ctx.beginPath();let prev;
 for(let i=start;i<end;i++){let y=base-Number(rows[i][key]||0)*25,x=95+(i-start)*step;if(perCycle&&key==='tck'){ctx.moveTo(x,base);ctx.lineTo(x+step/2,base);ctx.lineTo(x+step/2,base-25);ctx.lineTo(x+step,base-25);ctx.lineTo(x+step,base);continue;}if(i===start)ctx.moveTo(x,y);else{ctx.lineTo(x,prev);ctx.lineTo(x,y)}ctx.lineTo(x+step,y);prev=y}ctx.stroke();});
 ctx.strokeStyle='#e11d48';ctx.beginPath();ctx.moveTo(95+(n-start+.5)*step,5);ctx.lineTo(95+(n-start+.5)*step,245);ctx.stroke();
}
slider.oninput=show;document.getElementById('prev').onclick=()=>{slider.value=Math.max(0,Number(slider.value)-1);show()};document.getElementById('next').onclick=()=>{slider.value=Math.min(rows.length-1,Number(slider.value)+1);show()};show();
</script></html>'''

def render(csv_path, html_path, per_cycle=False):
    with Path(csv_path).open() as source:rows=list(csv.DictReader(source))
    if not rows:raise ValueError('Empty trace')
    Path(html_path).write_text(HTML.replace('__ROWS__',json.dumps(rows,ensure_ascii=False).replace('<','\\u003c')).replace('__CYCLE__',str(per_cycle).lower()))
