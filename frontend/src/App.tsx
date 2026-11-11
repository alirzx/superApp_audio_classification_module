import {useEffect,useState} from 'react';
interface Prediction {label_id:number;label:string;score:number}
interface Segment {start_seconds:number;end_seconds:number;predictions:Prediction[]}
interface Result {model:{id:string};audio:{duration_seconds:number;windows:number};predictions:Prediction[];segments:Segment[];processing_time_ms:number;warnings:string[]}
export default function App(){
 const [file,setFile]=useState<File|null>(null);
 const [url,setUrl]=useState('');
 const [threshold,setThreshold]=useState(.1);
 const [topK,setTopK]=useState(10);
 const [ready,setReady]=useState<boolean|null>(null);
 const [result,setResult]=useState<Result|null>(null);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 useEffect(()=>{let live=true;async function check(){try{const r=await fetch('/api/health/ready',{cache:'no-store'});if(live)setReady(r.ok)}catch{if(live)setReady(false)}}check();const timer=setInterval(check,20000);return()=>{live=false;clearInterval(timer)}},[]);
 useEffect(()=>{if(!file){setUrl('');return}const u=URL.createObjectURL(file);setUrl(u);return()=>URL.revokeObjectURL(u)},[file]);
 async function classify(){if(!file)return;setLoading(true);setError('');setResult(null);try{const body=new FormData();body.append('file',file);body.append('threshold',String(threshold));body.append('top_k',String(topK));const response=await fetch('/api/v1/classify',{method:'POST',body});if(!response.ok){let detail='HTTP '+response.status;try{const data=await response.json();detail=String(data.detail||detail)}catch{}throw new Error(detail)}setResult(await response.json())}catch(e){setError(e instanceof Error?e.message:'خطای نامشخص')}finally{setLoading(false)}}
 function save(){if(!result)return;const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download='audio-classification.json';a.click();URL.revokeObjectURL(u)}
 return <main className="layout"><header><span className="eyebrow">SUPERAPP • MODULE 07</span><h1>طبقه‌بندی رویدادهای صوتی</h1><p>شناسایی همزمان صداهای محیط، گفتار، موسیقی، وسایل نقلیه و صدها رویداد دیگر با EfficientAT روی CPU</p><span className={'status '+(ready?'ok':'warn')}>{ready===null?'بررسی سرویس…':ready?'● سرویس آماده':'● سرویس در دسترس نیست'}</span></header>
 <section className="panel"><h2>۱. فایل صوتی</h2><label className="upload"><input type="file" accept="audio/*,.wav,.mp3,.flac,.ogg,.m4a,.aac,.webm" onChange={e=>{setFile(e.target.files?.[0]||null);setResult(null);setError('')}}/><span>فایل صوتی خود را انتخاب کنید</span><small>WAV, MP3, FLAC, OGG, M4A, AAC, WebM • حداکثر ۲۰ مگابایت و ۶۰ ثانیه</small></label>{file&&<p>{file.name} ({(file.size/1024/1024).toFixed(2)} MB)</p>}{url&&<audio controls src={url} preload="metadata"/>}
 <div className="options"><label>حداقل امتیاز: {Math.round(threshold*100)}٪<input type="range" min="0" max="0.9" step="0.05" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/></label><label>تعداد نتایج<select value={topK} onChange={e=>setTopK(Number(e.target.value))}><option value={5}>۵</option><option value={10}>۱۰</option><option value={20}>۲۰</option></select></label></div><button onClick={classify} disabled={!file||loading||ready===false}>{loading?'در حال تحلیل…':'تحلیل فایل صوتی'}</button>{error&&<p role="alert" className="error">{error}</p>}</section>
 {result&&<section className="panel"><div className="row"><h2>۲. نتایج تحلیل</h2><button className="subtle" onClick={save}>خروجی JSON</button></div><p className="meta">مدل: {result.model.id} | مدت: {result.audio.duration_seconds.toFixed(1)} ثانیه | پنجره‌ها: {result.audio.windows} | زمان پردازش: {result.processing_time_ms} ms</p><h3>رویدادهای غالب</h3>{result.predictions.length?result.predictions.map(p=><div className="prediction" key={p.label_id}><div><span>{p.label}</span><strong>{Math.round(p.score*100)}٪</strong></div><div className="track"><div style={{width:(p.score*100)+'%'}}/></div></div>):<p>رویدادی بالاتر از آستانه یافت نشد.</p>}
 <h3>رویدادها در طول زمان</h3><div className="segments">{result.segments.map((s,i)=><div key={i} className="segment"><strong>{s.start_seconds.toFixed(1)}–{s.end_seconds.toFixed(1)} ثانیه</strong><span>{s.predictions.slice(0,3).map(p=>p.label+' ('+Math.round(p.score*100)+'٪)').join('، ')||'بدون رویداد با امتیاز کافی'}</span></div>)}</div><p className="hint">امتیازها احتمالات کالیبره‌شده نیستند و چند رویداد می‌توانند همزمان وجود داشته باشند.</p></section>}
 <footer>EfficientAT • AudioSet 527 labels • CPU only • No audio retained</footer></main>
}
