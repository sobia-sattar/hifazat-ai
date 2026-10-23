import {useState} from "react";
import {Link} from "react-router-dom";
import CommentDetail from "../components/CommentDetail";
import CommentTable from "../components/CommentTable";
import {api} from "../services/api";
import type {AnalysisPayload,CommentRow} from "../types";
export default function YoutubePage(){
const[url,setUrl]=useState("");const[data,setData]=useState<AnalysisPayload|null>(null);const[open,setOpen]=useState<CommentRow|null>(null);const[err,setErr]=useState("");const[loading,setLoading]=useState(false);
async function run(){setLoading(true);setErr("");try{const result=await api.analyzeYoutube(url);if(!result.ok)throw new Error("Analysis could not be completed");setData(result)}catch(e:any){setErr(e.message)}finally{setLoading(false)}}
async function latest(){setLoading(true);setErr("");try{const result=await api.latest();if(!result.ok)throw new Error(result.message||"No previous analysis");setData(result)}catch(e:any){setErr(e.message)}finally{setLoading(false)}}
const stats=data?.stats||{};const video=data?.video||{};
return <div className="video-workspace space-y-8"><section className="hero-grid"><div><span className="eyebrow"><span className="status-light"/> COMMENT INTELLIGENCE / HUMAN SUPERVISED</span><h1>Analyze video comments.</h1><p className="hero-description">Paste a video link to analyze its comments and review the results.</p>
<form className="scan-form" onSubmit={e=>{e.preventDefault();run()}}><label htmlFor="video-url" className="field-label">01 / START WITH A VIDEO</label><div className="scan-input"><span aria-hidden="true">▷</span><input id="video-url" type="text" required placeholder="YouTube video URL or 11-character video ID" value={url} onChange={e=>setUrl(e.target.value)}/><button className="btn" disabled={loading||!url.trim()}>{loading?"Analyzing…":"Analyze comments ↗"}</button></div></form>
<Link to="/youtube" className="text-button">Have a channel link? Open Channel scan →</Link><br/><button className="text-button" disabled={loading} onClick={latest}>Open last analysis →</button>{err&&<p role="alert" className="notice-error">{err}</p>}
</div></section>

{data?.demo_mode&&<div className="notice">Sample data only. A YouTube API key is required for real comments. <Link to="/settings">View connection status →</Link></div>}
{data?.ok&&<section className="space-y-5 result-in"><div className="section-heading"><div><span className="eyebrow">ANALYSIS RESULTS</span><h2>{video.title}</h2><p>{video.channel} · {data.demo_mode?"Sample analysis":"Fetched comments, not the full channel history"}</p></div>{data.analysis_id&&<a className="btn-ghost" href={api.exportUrl(data.analysis_id,"csv")}>Download CSV ↓</a>}</div>
<div className="stat-grid"><div className="stat-box"><small>Comments analyzed</small><strong>{stats.total??0}</strong></div><div className="stat-box"><small>Predicted safe</small><strong className="text-emerald-300">{stats.safe??0}</strong></div><div className="stat-box"><small>Predicted harmful</small><strong className="text-rose-300">{stats.bullying??0}</strong></div><div className="stat-box"><small>Uncertain</small><strong>{stats.uncertain??0}</strong></div></div>
{Number(stats.skipped)>0&&<p className="notice">{stats.skipped} empty or oversized comments were excluded from analysis.</p>}<CommentTable rows={data.comments||[]} onOpen={setOpen}/></section>}
{!data&&<div className="empty-inline"><span>↗</span><p>Your analysis appears here.<small>Only comments you fetch are examined. No automatic warnings or blocks.</small></p><Link to="/analyzer" className="btn-ghost">Try a single comment</Link></div>}
{open&&<CommentDetail row={open} onClose={()=>setOpen(null)}/>}</div>}

