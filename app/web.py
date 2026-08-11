from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def web_interface() -> HTMLResponse:
    return HTMLResponse(_PAGE)


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nexus AI Workspace</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#e8ecf7;background:#080b12;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 80% 0,#17203a 0,#080b12 42%)}
button,input{font:inherit}button{cursor:pointer}.shell{display:grid;grid-template-columns:240px 1fr;min-height:100vh}
aside{padding:24px 16px;border-right:1px solid #202738;background:#0b0f18cc;backdrop-filter:blur(14px)}
.brand{font-weight:800;font-size:20px;margin:0 8px 24px}.nav{display:grid;gap:6px}.nav button{border:0;background:transparent;color:#9ca8bd;text-align:left;padding:11px 12px;border-radius:10px}.nav button.active,.nav button:hover{background:#182033;color:#fff}
main{padding:28px;max-width:1400px;width:100%;margin:auto}.top{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:22px}.title{font-size:30px;font-weight:800;margin:0}.sub{color:#8995aa;margin:5px 0 0}.status{display:flex;gap:8px;align-items:center;color:#8fe0ad;font-size:13px}.dot{width:9px;height:9px;border-radius:50%;background:#42d77d;box-shadow:0 0 14px #42d77d}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{background:#101622d9;border:1px solid #202a3d;border-radius:16px;padding:18px;box-shadow:0 10px 35px #0003}.card h3{margin:0 0 7px}.metric{font-size:28px;font-weight:800}.muted{color:#7f8ba1;font-size:13px}.panel{margin-top:16px}.tools{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.tool{padding:13px;border:1px solid #263149;border-radius:12px;background:#0c111b}.tool b{display:block;font-size:13px}.tool span{color:#77849a;font-size:12px}.section{display:none}.section.active{display:block}.chat{display:grid;gap:12px;max-width:900px}.messages{min-height:320px;display:grid;align-content:end;gap:10px}.msg{max-width:78%;padding:12px 14px;border-radius:14px;background:#151c2b}.msg.user{margin-left:auto;background:#25406b}.composer{display:flex;gap:8px}.composer input{flex:1;background:#0c111b;border:1px solid #2a3449;color:#fff;padding:13px;border-radius:12px}.primary{border:0;border-radius:12px;padding:0 18px;background:#5d7cff;color:white;font-weight:700}.list{display:grid;gap:8px}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:13px;border:1px solid #232d41;border-radius:12px}.pill{padding:4px 8px;border-radius:999px;background:#18243b;color:#9fb8ff;font-size:11px}
@media(max-width:900px){.shell{grid-template-columns:1fr}aside{position:sticky;top:0;z-index:3;padding:10px;border-right:0;border-bottom:1px solid #202738}.brand{display:none}.nav{grid-template-columns:repeat(5,1fr)}.nav button{font-size:11px;text-align:center;padding:9px 4px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.tools{grid-template-columns:1fr 1fr}main{padding:18px}.title{font-size:24px}}
@media(max-width:520px){.grid,.tools{grid-template-columns:1fr}.top{align-items:flex-start}.status{font-size:11px}.messages{min-height:240px}.msg{max-width:90%}}
</style></head>
<body><div class="shell">
<aside><div class="brand">NEXUS AI</div><nav class="nav">
<button class="active" data-tab="overview">Home</button><button data-tab="chat">Chat</button><button data-tab="calendar">Calendar</button><button data-tab="tasks">Tasks</button><button data-tab="files">Files</button>
</nav></aside>
<main><div class="top"><div><h1 class="title">Nexus AI Workspace</h1><p class="sub">One responsive workspace for your agents, tools and daily work.</p></div><div class="status"><i class="dot"></i>Backend connected</div></div>
<section id="overview" class="section active"><div class="grid"><div class="card"><div class="muted">Tools</div><div class="metric" id="tool-count">…</div></div><div class="card"><div class="muted">Tasks</div><div class="metric" id="task-count">—</div></div><div class="card"><div class="muted">Meetings</div><div class="metric" id="meeting-count">—</div></div><div class="card"><div class="muted">Automations</div><div class="metric" id="automation-count">—</div></div></div><div class="card panel"><h3>Available tools</h3><div id="tools" class="tools"></div></div></section>
<section id="chat" class="section"><div class="card chat"><div class="messages" id="messages"><div class="msg">Hello. Nexus AI is ready.</div></div><form class="composer" id="chat-form"><input id="chat-input" aria-label="Message" placeholder="Ask Nexus AI…" autocomplete="off"><button class="primary">Send</button></form></div></section>
<section id="calendar" class="section"><div class="card"><h3>Calendar</h3><p class="muted">Your calendar integrations are available through the backend tools.</p><div class="list"><div class="row"><span>Calendar integration</span><span class="pill">Connected</span></div><div class="row"><span>Meeting integrations</span><span class="pill">Ready</span></div></div></div></section>
<section id="tasks" class="section"><div class="card"><h3>Tasks</h3><p class="muted">Task management is connected to the same tool registry.</p><div class="list"><div class="row"><span>Task workspace</span><span class="pill">Ready</span></div></div></div></section>
<section id="files" class="section"><div class="card"><h3>Files</h3><p class="muted">Files stay behind the existing permission and sandbox boundaries.</p><div class="list"><div class="row"><span>File workspace</span><span class="pill">Protected</span></div></div></div></section>
</main></div>
<script>
const tabs=[...document.querySelectorAll('[data-tab]')];const sections=[...document.querySelectorAll('.section')];
tabs.forEach(b=>b.onclick=()=>{tabs.forEach(x=>x.classList.toggle('active',x===b));sections.forEach(s=>s.classList.toggle('active',s.id===b.dataset.tab))});
async function loadTools(){try{const r=await fetch('/tools');const d=await r.json();document.getElementById('tool-count').textContent=d.tools.length;document.getElementById('tools').innerHTML=d.tools.map(t=>`<div class="tool"><b>${escapeHtml(t)}</b><span>Available</span></div>`).join('')}catch(e){document.getElementById('tool-count').textContent='offline'}}
function escapeHtml(v){return v.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
document.getElementById('chat-form').onsubmit=e=>{e.preventDefault();const i=document.getElementById('chat-input'),v=i.value.trim();if(!v)return;const box=document.getElementById('messages');box.insertAdjacentHTML('beforeend',`<div class="msg user">${escapeHtml(v)}</div><div class="msg">Message received. Connect an agent execution endpoint to enable live responses.</div>`);i.value='';box.lastElementChild.scrollIntoView({behavior:'smooth'})};
loadTools();
</script></body></html>"""
