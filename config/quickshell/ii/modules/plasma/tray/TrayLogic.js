// BWM: visibility semantics of Plasma systemtray (Auto/Shown/Hidden), keyed by stable SNI id.
function mode(settings,id) { const value=settings?.[id]; return ["shown","hidden"].includes(value)?value:"auto"; }
function visible(settings,id,active) { const m=mode(settings,id); return m==="shown" || (m==="auto"&&active); }
function update(settings,id,value) { const result=Object.assign({},settings); if(value==="auto")delete result[id];else result[id]=value;return result; }
