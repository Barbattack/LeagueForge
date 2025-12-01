# -*- coding: utf-8 -*-
from __future__ import annotations

import gspread
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any
from config import SHEET_ID
from utils_credentials import get_google_credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']

def _zfill(s, n=10): 
    return str(s).zfill(n)

def _to_float(x, default=0.0):
    try:
        s=str(x).strip()
        if s.endswith('%'):
            s=s[:-1]
        return float(s.replace(',','.'))
    except:
        return default

def _to_int(x, default=0):
    try:
        return int(float(str(x).replace(',','.').strip()))
    except:
        return default

def _parse_date_from_tid(tid):
    if not tid or '_' not in tid:
        return None
    part=tid.split('_',1)[1]
    for fmt in ('%Y%m%d','%Y-%m-%d','%d%m%Y','%Y.%m.%d'):
        try:
            return datetime.strptime(part, fmt)
        except:
            pass
    return None

def _tcg_from_season_id(season_id):
    pref=''
    for ch in str(season_id):
        if ch.isalpha():
            pref+=ch
        else:
            break
    return pref.upper()

def _stdev(vals):
    n=len(vals)
    if n<2:
        return 0.0
    m=sum(vals)/n
    return (sum((v-m)**2 for v in vals)/n)**0.5

def _connect_sheet():
    creds = get_google_credentials(scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

def _load_results(sheet):
    ws=sheet.worksheet("Results")
    rows=ws.get_all_values()[3:]
    results=[]; max_field=defaultdict(int); by_date={}
    for row in rows:
        if not row or len(row)<10:
            continue
        tid=row[1]
        if not tid:
            continue
        season_id = tid.split('_')[0] if '_' in tid else tid
        membership=_zfill(row[2],10)
        name=row[9] if len(row)>9 and row[9] else membership
        rank=_to_int(row[3],999)
        win_points=_to_float(row[4],0.0)
        omw=_to_float(row[5],0.0)
        pv=_to_float(row[6],0.0)
        pr=_to_float(row[7],0.0)
        pt=_to_float(row[8],0.0)
        date=_parse_date_from_tid(tid)
        field=int(max(0, pr+rank-1))
        if field>max_field[tid]:
            max_field[tid]=field
        if tid not in by_date:
            by_date[tid]=date
        results.append({
            "tid":tid,"season_id":season_id,"membership":membership,"name":name,
            "rank":rank,"win_points":win_points,"omw":omw,"pv":pv,"pr":pr,"pt":pt,"date":date
        })
    events={tid:{"date":by_date.get(tid),"participants":p} for tid,p in max_field.items()}
    return results, events

def _scope_records(res, scope):
    if str(scope).startswith("ALL-"):
        tcg=str(scope).split('-',1)[1].upper()
        return [r for r in res if _tcg_from_season_id(r["season_id"])==tcg]
    return [r for r in res if r["season_id"]==scope]

def _events_in_scope(events, records):
    tids={r["tid"] for r in records}
    return {tid: events[tid] for tid in tids if tid in events}

def _compute_for_scope(scope, res, events):
    recs=_scope_records(res, scope)
    evs=_events_in_scope(events, recs)

    # spotlights (numeriche)
    by_player=defaultdict(list)
    for r in recs:
        by_player[r["membership"]].append(r)
    participants=[e["participants"] for e in evs.values() if e["participants"]>0]
    q3=sorted(participants)[int(0.75*(len(participants)-1))] if participants else 0
    mvp=[]; sharp=[]; metro=[]; phoenix=[]; bigs=[]; clos=[]
    events_per_player={m:len(v) for m,v in by_player.items() if v}
    avg_events=(sum(events_per_player.values())/len(events_per_player)) if events_per_player else 1.0
    for m,evts in by_player.items():
        # name più frequente
        names=[e["name"] for e in evts]
        name = max(set(names), key=names.count) if names else m
        pts=[e["pt"] for e in evts]; n=len(pts)
        mean_pts=(sum(pts)/n) if n else 0.0; st=_stdev(pts)
        mvp_score=mean_pts*((n/avg_events) if avg_events>0 else 1.0)
        mvp.append({"membership":m,"name":name,"score":round(mvp_score,2),"events":n})
        sharp.append({"membership":m,"name":name,"score":round(mean_pts,2),"events":n})
        metro.append({"membership":m,"name":name,"score":round(st,2),"events":n})

        # rising_star: miglioramento ranking stagionale (placeholder per ora)
        # Calcolo trend punti come proxy
        evts_sorted=sorted(evts, key=lambda e: (e["date"] or datetime.min, e["tid"]))
        pts_sorted=[e["pt"] for e in evts_sorted]
        if len(pts_sorted)>=3:
            recent_avg=sum(pts_sorted[-2:])/2
            older_avg=sum(pts_sorted[:-2])/len(pts_sorted[:-2])
            rs_score=recent_avg-older_avg
        else:
            rs_score=0.0
        phoenix.append({"membership":m,"name":name,"score":round(rs_score,2),"events":n})

        # big stage: media punti sugli eventi nel quartile superiore per partecipanti
        if q3>0:
            big_evts=[e for e in evts if evs.get(e["tid"],{}).get("participants",0)>=q3]
            bs=(sum(e["pt"] for e in big_evts)/len(big_evts)) if big_evts else 0.0
        else:
            bs=0.0
        bigs.append({"membership":m,"name":name,"score":round(bs,2),"events":n})

        # closer: quota punti da Top 8
        top8_pts=sum(e["pt"] for e in evts if e["rank"]<=8); tot=sum(pts)
        clos.append({"membership":m,"name":name,"score":round((top8_pts/tot) if tot>0 else 0.0,3),"events":n})

    def topn(lst, reverse=True, n=10, min_events=3):
        flt=[x for x in lst if x["events"]>=min_events]
        return sorted(flt, key=lambda x: x["score"], reverse=reverse)[:n]

    # Costante vs Imprevedibile (top1 di ciascuno)
    most_consistent = topn(metro, False, n=1, min_events=3)
    most_volatile = topn(metro, True, n=1, min_events=3)
    
    spot = {
        "dominatore": topn(mvp, True, n=5),
        "cecchino": topn(sharp, True, n=5),
        "costante_vs_imprevedibile": {
            "costante": most_consistent[0] if most_consistent else None,
            "imprevedibile": most_volatile[0] if most_volatile else None
        },
        "fenice": topn(phoenix, True, n=5),
        "big_match_player": topn(bigs, True, n=5),
        "finalista": topn(clos, True, n=5),
    }

    # narrative
    name_of = {}
    first_date = {}
    for r in recs:
        m = r["membership"]
        name_of[m] = r.get("name", m)
        d = r.get("date")
        if d and (m not in first_date or d < first_date[m]):
            first_date[m] = d

    evlist = sorted([(tid, e.get("date")) for tid, e in evs.items()], key=lambda x: (x[1] or datetime.min, x[0]))
    last_tid = evlist[-1][0] if len(evlist) >= 1 else None
    prev_tid = evlist[-2][0] if len(evlist) >= 2 else None
    last_date = evlist[-1][1] if len(evlist) >= 1 else None

    # Ironman
    ironman_m = None; ironman_n = 0
    for m, evts in by_player.items():
        n = len(evts)
        if n > ironman_n:
            ironman_n = n; ironman_m = m
    ironman = None
    if ironman_m:
        ironman = {"name": name_of.get(ironman_m, ironman_m), "events": ironman_n}

    # Rookie (<=3 eventi con migliore top8 rate)
    rookie = None
    cand = []
    for m, evts in by_player.items():
        n = len(evts)
        if n <= 3 and n > 0:
            top8 = sum(1 for e in evts if (e.get("rank") or 999) <= 8)
            rate = (top8 / n) if n else 0.0
            cand.append((rate, top8, n, m))
    if cand:
        cand.sort(reverse=True)
        rate, top8, n, m = cand[0]
        rookie = {"name": name_of.get(m, m), "top8": int(top8), "events": int(n), "rate_pct": round(rate*100,1)}

    # Climber (evento vs precedente)
    climber_ev = None
    if last_tid and prev_tid:
        rank_last = {}; rank_prev = {}
        for r in recs:
            if r.get("tid")==last_tid: rank_last[r["membership"]] = r.get("rank") or 999
            if r.get("tid")==prev_tid: rank_prev[r["membership"]] = r.get("rank") or 999
        deltas = []
        for m in set(rank_last.keys()) & set(rank_prev.keys()):
            d = (rank_prev[m] - rank_last[m])
            deltas.append((d, m))
        deltas.sort(reverse=True)
        if deltas and deltas[0][0] > 0:
            d, m = deltas[0]
            climber_ev = {"name": name_of.get(m, m), "delta": int(d)}

    # Climber (mese su mese)
    climber_mom = None
    if last_date:
        cur_month = (last_date.year, last_date.month)
        py, pm = last_date.year, last_date.month - 1
        if pm == 0:
            py -= 1; pm = 12
        prev_month = (py, pm)
        by_mo = {}
        for r in recs:
            d = r.get("date")
            if not d: 
                continue
            key = (d.year, d.month, r["membership"])
            by_mo.setdefault(key, []).append(r.get("rank") or 999)
        avg_rank = {}
        for (y,m,mem), ranks in by_mo.items():
            avg_rank[(y,m,mem)] = sum(ranks)/len(ranks)
        deltas = []
        mems = {mem for (y,m,mem) in avg_rank.keys() if (y,m) in [cur_month, prev_month]}
        for mem in mems:
            a = avg_rank.get((prev_month[0], prev_month[1], mem))
            b = avg_rank.get((cur_month[0], cur_month[1], mem))
            if a is not None and b is not None:
                d = a - b
                deltas.append((d, mem))
        deltas.sort(reverse=True)
        if deltas and deltas[0][0] > 0:
            d, m = deltas[0]
            climber_mom = {"name": name_of.get(m, m), "delta": round(d,1)}

    # New Faces (30g)
    new_faces = {"count": 0, "examples": []}
    if last_date:
        start = last_date - timedelta(days=30)
        newcomers = [m for m, fd in first_date.items() if fd and fd >= start]
        new_faces["count"] = len(newcomers)
        ex = sorted(newcomers, key=lambda m: first_date[m], reverse=True)[:3]
        import re
        def _clean(n):
            try:
                return re.sub(r"\[[^\]]+\]\s*","",str(n)).strip()
            except Exception:
                return str(n)
        new_faces["examples"] = [_clean(name_of.get(m,m)) for m in ex]

    # Attendance Pulse (30g)
    attendance = None
    if last_date and evlist:
        start = last_date - timedelta(days=30)
        prev_start = start - timedelta(days=30)
        cur_vals = [ (tid, evs[tid].get("participants") or 0) for tid, d in evlist if d and d>start ]
        prev_vals = [ (tid, evs[tid].get("participants") or 0) for tid, d in evlist if d and (prev_start<d<=start) ]
        cur_avg = round( (sum(v for _,v in cur_vals)/len(cur_vals)) ,1) if cur_vals else 0.0
        prev_avg = round( (sum(v for _,v in prev_vals)/len(prev_vals)) ,1) if prev_vals else 0.0
        trend = round(cur_avg - prev_avg,1)
        attendance = {"avg": cur_avg, "trend": trend, "n": len(cur_vals)}

    # Compose narrative
    spot_narrative = []
    # Rising Star
    rising = spot.get("fenice", [])[:1]
    if rising:
        r = rising[0]
        spot_narrative.append({
            "id":"rising_star","icon":"⭐","title":"Rising Star",
            "text": f"{r.get('name')} è in crescita.",
            "proof": f"Trend +{r.get('score',0)} pt negli ultimi tornei",
            "tag": "min 3 eventi","tooltip":"Differenza tra media ultimi 2 tornei e media precedenti."
        })
    else:
        spot_narrative.append({
            "id":"rising_star","icon":"⭐","title":"Rising Star",
            "text":"Serve più dati.","proof":"",
            "tag":"", "tooltip":"Serve almeno 3 eventi."
        })
    # Rookie
    if rookie:
        spot_narrative.append({
            "id":"rookie","icon":"🚀","title":"Rookie to Watch",
            "text": f"{rookie['name']} debutta forte.",
            "proof": f"Top 8: {rookie['top8']}/{rookie['events']} ({rookie['rate_pct']}%)",
            "tag":"≤3 eventi", "tooltip":"Giocatori con al massimo 3 eventi in stagione; ordinati per percentuale di Top 8."
        })
    else:
        spot_narrative.append({
            "id":"rookie","icon":"🚀","title":"Rookie to Watch",
            "text":"Nessun rookie con abbastanza eventi.","proof":"",
            "tag":"", "tooltip":"Serve almeno 1 evento per essere considerati rookie."
        })
    # Ironman
    if ironman:
        spot_narrative.append({
            "id":"ironman","icon":"🧱","title":"Ironman",
            "text": f"{ironman['name']} sempre presente.",
            "proof": f"{ironman['events']} eventi giocati",
            "tag":"stagione", "tooltip":"Giocatore con più eventi giocati nella stagione selezionata."
        })
    else:
        spot_narrative.append({"id":"ironman","icon":"🧱","title":"Ironman","text":"N/A","proof":"","tag":"","tooltip":""})
    # Climber
    climber_text = "N/A"; climber_proof = ""; climber_tag = "min 2 eventi recenti"
    if climber_ev or climber_mom:
        parts = []
        if climber_ev: parts.append(f"Δ evento: +{climber_ev['delta']} pos ({climber_ev['name']})")
        if climber_mom: parts.append(f"Δ mese: +{climber_mom['delta']} pos ({climber_mom['name']})")
        climber_text = " • ".join(parts)
        climber_proof = "Miglior rimonta su evento e/o mese"
    spot_narrative.append({
        "id":"climber","icon":"📈","title":"Climber",
        "text": climber_text, "proof": climber_proof, "tag": climber_tag,
        "tooltip":"Δ evento: differenza di posizioni tra ultimo e penultimo evento. Δ mese: media posizioni mese corrente vs precedente."
    })
    # Closer
    clo = spot.get("closer", [])[:1]
    if clo:
        c=clo[0]; pct = round((c.get("score",0.0))*100,1)
        spot_narrative.append({
            "id":"closer","icon":"🎯","title":"Closer",
            "text": f"{c.get('name')} capitalizza nelle fasi finali.",
            "proof": f"{pct}% dei punti arriva da Top 8",
            "tag":"min 3 eventi", "tooltip":"Quota punti conquistata quando il giocatore finisce in Top 8."
        })
    else:
        spot_narrative.append({"id":"closer","icon":"🎯","title":"Closer","text":"N/A","proof":"","tag":"","tooltip":""})
    # Big Stage
    bs = spot.get("big_stage", [])[:1]
    if bs:
        b=bs[0]
        spot_narrative.append({
            "id":"big_stage","icon":"🏟️","title":"Big Stage",
            "text": f"{b.get('name')} rende al meglio nei grandi eventi.",
            "proof": f"Media {b.get('score',0)} pt/evento (Q3 partecipanti)",
            "tag":"min 3 eventi", "tooltip":"Media punti sugli eventi nel quartile superiore per partecipazione."
        })
    else:
        spot_narrative.append({"id":"big_stage","icon":"🏟️","title":"Big Stage","text":"N/A","proof":"","tag":"","tooltip":""})
    # New Faces
    if new_faces and new_faces["count"]>0:
        names = ", ".join(new_faces["examples"])
        spot_narrative.append({
            "id":"new_faces","icon":"👥","title":"New Faces (30g)",
            "text": f"{new_faces['count']} nuovi giocatori.",
            "proof": names, "tag":"ultimi 30g",
            "tooltip":"Giocatori al primo evento negli ultimi 30 giorni (rispetto alla data dell'ultimo evento)."
        })
    else:
        spot_narrative.append({"id":"new_faces","icon":"👥","title":"New Faces (30g)","text":"Nessun nuovo giocatore nell'ultimo mese.","proof":"","tag":"","tooltip":""})
    # Attendance Pulse
    if attendance:
        t = ("+" if attendance["trend"]>0 else "") + str(attendance["trend"])
        spot_narrative.append({
            "id":"attendance_pulse","icon":"📊","title":"Attendance Pulse",
            "text": f"Media {attendance['avg']} partecipanti.",
            "proof": f"Trend {t} vs mese precedente ({attendance['n']} eventi)",
            "tag":"30g", "tooltip":"Media partecipanti negli ultimi 30 giorni e differenza con i 30 giorni precedenti."
        })
    else:
        spot_narrative.append({"id":"attendance_pulse","icon":"📊","title":"Attendance Pulse","text":"N/A","proof":"","tag":"","tooltip":""})

    # pulse KPI
    kpi={}
    kpi["events_total"]=len(evs)
    kpi["unique_players"]=len({r["membership"] for r in recs})
    kpi["entries_total"]=len(recs)
    parts=[e["participants"] for e in evs.values() if e["participants"]>0]
    kpi["avg_participants"]=round(sum(parts)/len(parts),2) if parts else 0.0
    top8=sum(1 for r in recs if r["rank"]<=8)
    kpi["top8_rate"]=round((top8/len(recs))*100,2) if recs else 0.0
    omws=[r["omw"] for r in recs if r["omw"] is not None]
    kpi["avg_omw"]=round(sum(omws)/len(omws),2) if omws else 0.0
    
    # Compleanno Lega - uso evlist_simple prima di ridefinirlo
    evlist_simple = sorted([(tid, e.get("date")) for tid, e in evs.items()], key=lambda x: (x[1] or datetime.min, x[0]))
    if evlist_simple:
        first_event_date = min((d for _,d in evlist_simple if d), default=None)
        last_event_date = max((d for _,d in evlist_simple if d), default=None)
        if first_event_date and last_event_date:
            giorni_attivi = (last_event_date - first_event_date).days
            kpi["compleanno_lega"] = {
                "giorni": giorni_attivi,
                "primo_torneo": first_event_date.isoformat(),
                "ultimo_torneo": last_event_date.isoformat()
            }
        else:
            kpi["compleanno_lega"] = None
    else:
        kpi["compleanno_lega"] = None
    
    # Record Presenze
    if parts:
        max_part = max(parts)
        # Trova torneo con max presenze
        for tid, e in evs.items():
            if e["participants"] == max_part:
                kpi["record_presenze"] = {
                    "count": max_part,
                    "tid": tid,
                    "date": e.get("date").isoformat() if e.get("date") else ""
                }
                break
    else:
        kpi["record_presenze"] = None

    by_tid_pts=defaultdict(list)
    for r in recs:
        by_tid_pts[r["tid"]].append(r["pt"])
    evlist=[(tid, e["date"], e["participants"]) for tid,e in evs.items()]
    evlist.sort(key=lambda x:(x[1] or datetime.min, x[0]))
    series_entries=[]; series_avg=[]
    for tid,d,participants in evlist:
        pts=by_tid_pts.get(tid,[])
        avg=(sum(pts)/len(pts)) if pts else 0.0
        series_entries.append({"tid":tid,"date": d.isoformat() if d else "","participants":participants})
        series_avg.append({"tid":tid,"date": d.isoformat() if d else "","avg_points": round(avg,2)})
    pulse={"kpi":kpi,"series":{"entries_per_event":series_entries,"avg_points_per_event":series_avg}}

    # tales
    by_event_players=defaultdict(list); by_event_podium=defaultdict(list); by_event_top8=defaultdict(list); name_of={}
    def pairs(L):
        out=[]; L=list(L)
        for i in range(len(L)):
            for j in range(i+1,len(L)):
                a,b=L[i],L[j]
                if a==b: continue
                if a<b: out.append((a,b))
                else: out.append((b,a))
        return out
    for r in recs:
        by_event_players[r["tid"]].append(r["membership"])
        if r["rank"]<=3: by_event_podium[r["tid"]].append(r["membership"])
        if r["rank"]<=8: by_event_top8[r["tid"]].append(r["membership"])
        name_of[r["membership"]]=r["name"]
    co=Counter(); rp=Counter(); mix=defaultdict(set)
    for tid, players in by_event_players.items():
        for a,b in pairs(players): co[(a,b)]+=1
    for tid, podium in by_event_podium.items():
        for a,b in pairs(podium): rp[(a,b)]+=1
    for tid, top8 in by_event_top8.items():
        s=set(top8)
        for p in s: mix[p].update(s-{p})
    def fmt(cnt, topn=10):
        out=[]
        for (a,b), c in cnt.most_common(topn):
            out.append({"a":{"membership":a,"name":name_of.get(a,a)},"b":{"membership":b,"name":name_of.get(b,b)},"count":int(c)})
        return out
    companions=fmt(co,10); rivals=fmt(rp,10)
    mixture=[{"membership":m,"name":name_of.get(m,m),"unique_opponents":len(s)} for m,s in mix.items()]
    mixture.sort(key=lambda x: x["unique_opponents"], reverse=True); mixture=mixture[:10]
    tales={
        "companions":companions,
        "podium_rivals":rivals,
        "top8_mixture":mixture,
        "sfortuna_nera": None,
        "torneo_competitivo": None,
        "ultimo_arrivato": None
    }
    
    # Sfortuna Nera: 9° posto (fuori top8 per 1)
    nono_posti = defaultdict(int)
    for r in recs:
        if r["rank"] == 9:
            nono_posti[r["membership"]] += 1
    if nono_posti:
        top_sfortuna = max(nono_posti.items(), key=lambda x: x[1])
        m, cnt = top_sfortuna
        tales["sfortuna_nera"] = {"membership": m, "name": name_of.get(m,m), "count": cnt}
    
    # Torneo Competitivo: più giocatori con record positivo in top8
    torneo_comp = None
    best_comp_score = 0
    for tid, players in by_event_top8.items():
        top8_recs = [r for r in recs if r["tid"]==tid and r["rank"]<=8]
        # Conta quanti hanno win_points >= media
        if top8_recs:
            avg_wp = sum(r["win_points"] for r in top8_recs) / len(top8_recs)
            positive = sum(1 for r in top8_recs if r["win_points"] >= avg_wp)
            comp_score = positive * evs[tid].get("participants", 0)
            if comp_score > best_comp_score:
                best_comp_score = comp_score
                date_obj = evs[tid].get("date")
                torneo_comp = {
                    "tid": tid,
                    "date": date_obj.isoformat() if date_obj else None,
                    "participants": evs[tid].get("participants", 0),
                    "balanced_top8": positive
                }
    tales["torneo_competitivo"] = torneo_comp
    
    # Ultimo Arrivato
    if first_date:
        ultimo_m = max(first_date.items(), key=lambda x: x[1])
        m, d = ultimo_m
        tales["ultimo_arrivato"] = {"membership": m, "name": name_of.get(m,m), "date": d.isoformat() if d else ""}

    # HOF
    highest=None; biggest=None; most_bal=None; most_dom=None
    for r in recs:
        if (highest is None) or (r["pt"]>highest["pt"]):
            highest={"membership":r["membership"],"name":r["name"],"pt":r["pt"],"tid":r["tid"]}
    for tid,e in evs.items():
        if (biggest is None) or (e["participants"]>biggest["participants"]):
            biggest={"tid":tid,"participants":e["participants"]}
    for tid,pts in by_tid_pts.items():
        if len(pts)<8: continue
        sdev=_stdev(pts)
        if (most_bal is None) or (sdev<most_bal["stdev"]):
            most_bal={"tid":tid,"stdev":round(sdev,2),"participants":len(pts)}
    for tid,pts in by_tid_pts.items():
        if len(pts)<8: continue
        s=sorted(pts, reverse=True); gap=s[0]-s[7]
        if (most_dom is None) or (gap>most_dom["gap"]):
            most_dom={"tid":tid,"gap":round(gap,2),"participants":len(pts)}
    best_ph=None
    by_pl=defaultdict(list)
    for r in recs:
        by_pl[r["membership"]].append(r)
    for m,evts in by_pl.items():
        evts_sorted=sorted(evts, key=lambda e: (e["date"] or datetime.min, e["tid"]))
        pts_sorted=[e["pt"] for e in evts_sorted]
        if len(pts_sorted)>=2:
            last3=pts_sorted[-3:] if len(pts_sorted)>=3 else pts_sorted[-2:]
            prev=pts_sorted[:-3] if len(pts_sorted)>=4 else pts_sorted[:-2]
            prev_mean=(sum(prev)/len(prev)) if prev else 0.0
            ph=sum(last3)/len(last3)-prev_mean
            if (best_ph is None) or (ph>best_ph["score"]):
                name=max((e["name"] for e in evts), key=lambda n: sum(1 for e in evts if e["name"]==n), default=m)
                best_ph={"membership":m,"name":name,"score":round(ph,2)}

    hof={
        "highest_single_score":highest,
        "biggest_crowd":biggest,
        "most_balanced":most_bal,
        "most_dominated":most_dom,
        "fastest_riser":best_ph,
        "underdog_hero": None,
        "scalata_epica": None,
        "piu_vittorie": None,
        "piu_punti": None
    }
    
    # Underdog Hero: vittorie da fondo classifica (rank iniziale alto, finisce 1°)
    # Approssimazione: chi vince con seed basso = tanti partecipanti - ranking finale
    underdog_wins = []
    for r in recs:
        if r["rank"] == 1:
            participants = evs[r["tid"]].get("participants", 0)
            # Seed basso = participants alto e ranking 1
            if participants >= 10:  # Almeno 10 partecipanti
                underdog_wins.append({
                    "membership": r["membership"],
                    "name": r["name"],
                    "tid": r["tid"],
                    "participants": participants
                })
    if underdog_wins:
        # Conta quante volte ha vinto da underdog
        underdog_count = Counter(w["membership"] for w in underdog_wins)
        top_underdog = max(underdog_count.items(), key=lambda x: x[1])
        m, cnt = top_underdog
        hof["underdog_hero"] = {"membership": m, "name": name_of.get(m, m), "wins": cnt}
    
    # Scalata Epica: maggior salto posizioni in classifica stagionale
    # Serve standings, ma qui non abbiamo accesso. Usiamo proxy: delta rank tra primo e ultimo torneo
    scalata_candidates = []
    for m, evts in by_pl.items():
        if len(evts) >= 3:
            evts_sorted = sorted(evts, key=lambda e: (e["date"] or datetime.min, e["tid"]))
            first_rank = evts_sorted[0]["rank"]
            last_rank = evts_sorted[-1]["rank"]
            delta = first_rank - last_rank
            if delta > 0:  # Miglioramento
                scalata_candidates.append({
                    "membership": m,
                    "name": name_of.get(m, m),
                    "delta": delta,
                    "events": len(evts)
                })
    if scalata_candidates:
        scalata_candidates.sort(key=lambda x: x["delta"], reverse=True)
        hof["scalata_epica"] = scalata_candidates[0]
    
    # Più Vittorie (rank=1)
    vittorie_count = Counter()
    for r in recs:
        if r["rank"] == 1:
            vittorie_count[r["membership"]] += 1
    if vittorie_count:
        top_vitt = max(vittorie_count.items(), key=lambda x: x[1])
        m, cnt = top_vitt
        hof["piu_vittorie"] = {"membership": m, "name": name_of.get(m, m), "wins": cnt}
    
    # Più Punti Lifetime
    punti_lifetime = defaultdict(float)
    for r in recs:
        punti_lifetime[r["membership"]] += r["pt"]
    if punti_lifetime:
        top_punti = max(punti_lifetime.items(), key=lambda x: x[1])
        m, pts = top_punti
        hof["piu_punti"] = {"membership": m, "name": name_of.get(m, m), "points": round(pts, 2)}

    return {"spotlights":spot,"spot_narrative":spot_narrative,"pulse": {"kpi": kpi, "series": {"entries_per_event": series_entries, "avg_points_per_event": series_avg}}, "tales":tales,"hof":hof}


def build_stats(scopes):
    """
    Compatibilità:
    - Se `scopes` è una stringa come 'OP12', viene trattata come lista con un solo elemento.
    - Ritorna sempre un dict {scope: payload}. (La tua app può "spianare" se vuole un payload piatto.)
    """
    sheet=_connect_sheet()
    res, events=_load_results(sheet)

    if isinstance(scopes, (list, tuple, set)):
        targets = [str(s) for s in scopes]
    else:
        targets = [str(scopes)]

    out = {}
    for scope in targets:
        out[scope] = _compute_for_scope(scope, res, events)
    return out
