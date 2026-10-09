let scenario = null;
let selectedId = null;
const $ = id => document.getElementById(id);
async function api(url, body) {
  const options = body ? {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)} : {};
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}
function toast(msg){$("toast").textContent=msg;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),2400)}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function render(){
  if(!scenario)return;
  $("scenarioId").textContent=scenario.id;
  $("envReadout").textContent=scenario.environment;
  $("weatherReadout").textContent=scenario.weather;
  $("trackCount").textContent=scenario.objects.length;
  $("reviewCount").textContent=`${Object.keys(scenario.actions||{}).length} reviewed`;
  $("tracks").innerHTML="";
  $("trackList").innerHTML="";
  scenario.objects.forEach((o,i)=>{
    const marker=document.createElement("button");
    marker.className="track-marker"+(o.id===selectedId?" selected":"")+(scenario.actions[o.id]?" reviewed":"");
    marker.style.left=o.x+"%"; marker.style.top=o.y+"%"; marker.title=o.id;
    marker.setAttribute("aria-label","Select "+o.id); marker.onclick=()=>selectTrack(o.id);
    $("tracks").appendChild(marker);
    const row=document.createElement("div");
    row.className="track-row"+(o.id===selectedId?" active":"");
    row.innerHTML=`<div class="track-symbol">${String(i+1).padStart(2,"0")}</div><div><strong>${escapeHtml(o.id)}</strong><small>${escapeHtml(o.kind)} · ${escapeHtml(o.behavior)}</small>${scenario.actions[o.id]?'<div class="review-tag">✓ DECISION RECORDED</div>':''}</div><div class="track-meta"><b>${o.confidence}%</b><small>confidence</small></div>`;
    row.onclick=()=>selectTrack(o.id);
    $("trackList").appendChild(row);
  });
  if(scenario.status==="completed"){$("submitAction").disabled=true;$("finish").disabled=true}
  else {$("submitAction").disabled=false;$("finish").disabled=false}
  if(selectedId)fillSelected();
}
function selectTrack(id){
  selectedId=id;
  $("noSelection").classList.add("hidden");$("decisionForm").classList.remove("hidden");
  render();
}
function fillSelected(){
  const o=scenario.objects.find(x=>x.id===selectedId);if(!o)return;
  $("selectedId").textContent=o.id;$("selectedKind").textContent=o.kind;
  $("selectedConfidence").textContent=o.confidence+"%";$("confidenceMeter").style.width=o.confidence+"%";
  $("selectedSignal").textContent=o.signal;$("selectedBehavior").textContent=o.behavior;
  const a=scenario.actions[o.id];
  $("classification").value=a?a.classification:"Threat";
  $("response").value=a?a.response:(o.signal==="High"?"Notify supervisor":"Continue monitoring");
  $("actionMessage").textContent=a?"Decision already recorded. You can update it before finishing.":"";
}
async function generate(){
  try{
    scenario=await api("/api/scenario",{environment:$("environment").value,weather:$("weather").value,difficulty:$("difficulty").value,threat_mode:$("threat_mode").value});
    selectedId=scenario.objects[0]?.id||null;
    $("aarStatus").textContent="RUN ACTIVE";$("export").classList.add("disabled");
    $("finish").disabled=false;$("submitAction").disabled=false;
    $("aarContent").innerHTML='<div class="aar-placeholder"><div class="placeholder-icon">◎</div><strong>Scenario is running.</strong><p>Review every track, record your decisions, then finish the run to generate the AAR.</p></div>';
    $("noSelection").classList.add("hidden");$("decisionForm").classList.remove("hidden");
    render();toast("Scenario generated: "+scenario.id);
  }catch(e){toast(e.message)}
}
$("generate").onclick=generate;
$("submitAction").onclick=async()=>{
  if(!selectedId||!scenario)return toast("Generate a scenario and select a track first.");
  try{
    scenario=await api("/api/action",{track_id:selectedId,classification:$("classification").value,response:$("response").value});
    render();$("actionMessage").textContent="Decision saved to this training run.";
    toast("Decision recorded");
  }catch(e){toast(e.message)}
};
$("finish").onclick=async()=>{
  try{
    const report=await api("/api/finish");
    $("aarStatus").textContent="RUN COMPLETE";$("export").classList.remove("disabled");
    $("aarContent").innerHTML=`<div class="score-layout"><div class="score-circle"><strong>${report.score}</strong><small>OUT OF 100</small></div><div class="score-copy"><h3>${report.score>=80?"Strong decision performance":report.score>=55?"Developing performance":"Review recommended"}</h3><p>Score combines classification correctness and proportionate response choices. It is a training metric, not a real-world readiness certification.</p></div></div><div class="aar-metrics"><div class="aar-metric"><strong>${report.correct}/${report.total}</strong><small>Correct classifications</small></div><div class="aar-metric"><strong>${report.reviewed}/${report.total}</strong><small>Tracks reviewed</small></div><div class="aar-metric"><strong>${report.total-report.reviewed}</strong><small>Unreviewed tracks</small></div></div><div class="recommend">${escapeHtml(report.recommendation)}</div><table class="detail-table"><thead><tr><th>TRACK</th><th>REFERENCE LABEL</th><th>YOUR CALL</th><th>RESULT</th></tr></thead><tbody>${report.details.map(d=>`<tr><td>${escapeHtml(d.track_id)}</td><td>${escapeHtml(d.truth)}</td><td>${escapeHtml(d.classification)}</td><td class="${d.result==="Correct"?"result-good":"result-bad"}">${escapeHtml(d.result)}</td></tr>`).join("")}</tbody></table>`;
    scenario.status="completed";render();toast("After-Action Review generated");
  }catch(e){toast(e.message)}
};
(async()=>{try{const old=await api("/api/scenario");if(old&&old.objects){scenario=old;selectedId=old.objects[0]?.id||null;if(selectedId){$("noSelection").classList.add("hidden");$("decisionForm").classList.remove("hidden")}render();if(old.report){$("aarStatus").textContent="RUN COMPLETE";$("export").classList.remove("disabled")}}}catch(e){}})();
