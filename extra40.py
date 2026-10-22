# Current 40-man players that FanGraphs' payroll pages don't list (and aren't prospects / pending free agents).
import json,re,urllib.request,unicodedata
def norm(s): return re.sub(r'[^a-z ]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().replace('.','').replace('-',' ')).strip()
def names(o,acc):
    if isinstance(o,dict):
        n=o.get('n'); 
        if isinstance(n,str): acc.add(norm(n))
        for v in o.values(): names(v,acc)
    elif isinstance(o,list):
        for v in o: names(v,acc)
    return acc
def get(u):
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'roster-tool'}),timeout=30))
        except Exception as e: err=e
    raise err
def build(teams,index_html,league,sim):
    src=open(index_html,encoding='utf-8').read()
    known=names(league,set())|names(sim,set())
    for key in ('PROSPECTS','FA_TRACKER'):
        i=src.index('const '+key+' = ')+len('const '+key+' = '); j=src.index('\n',i)
        arr=json.loads(src[i:j].rstrip(';'))
        for x in arr: known.add(norm(x[0] if isinstance(x,list) else x['n']))
    extra=[]; live={}; ids={}
    for nick,tid in teams.items():
        r=get(f'https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=40Man&hydrate=person')['roster']
        if len(r)<35: raise RuntimeError('short roster '+nick)
        for x in r:
            p=x['person']; k=norm(p['fullName']); live.setdefault(k,nick); ids[k]=p['id']
            if k not in known:
                extra.append([p['fullName'],nick,p.get('currentAge'),x['position']['abbreviation'],x['status']['code'],p['id']])
    return sorted(extra,key=lambda r:(r[1],r[0])),live,ids

def poshist(ids,min_games=10):
    """Positions each player has actually played in MLB (career fielding games >= min_games, pitchers/DH aside from DH itself)."""
    out={}; items=list(ids.items())
    for i in range(0,len(items),50):
        chunk=items[i:i+50]
        d=get('https://statsapi.mlb.com/api/v1/people?personIds='+','.join(str(v) for _,v in chunk)+'&hydrate=stats(group=%5Bfielding%5D,type=%5Bcareer%5D)')
        for p in d.get('people',[]):
            g={}
            for st in p.get('stats',[]):
                for sp in st.get('splits',[]):
                    a=(sp.get('position') or {}).get('abbreviation'); n=sp['stat'].get('games') or 0
                    if a and a not in ('P','TWP') and n>=min_games: g[a]=g.get(a,0)+n
            if g: out[' '.join(w for w in norm(p['fullName']).split() if w not in ('jr','sr','ii','iii'))]=[a for a,_ in sorted(g.items(),key=lambda x:-x[1])]
    # pitchers: starter or reliever, from this season's (else career) games started vs. games pitched
    for i in range(0,len(items),50):
        chunk=items[i:i+50]
        d=get('https://statsapi.mlb.com/api/v1/people?personIds='+','.join(str(v) for _,v in chunk)+'&hydrate=stats(group=%5Bpitching%5D,type=%5Bseason,career%5D,season=2026)')
        for p in d.get('people',[]):
            by={}
            for st in p.get('stats',[]):
                t=(st.get('type') or {}).get('displayName')
                for sp in st.get('splits',[]):
                    if t in ('season','career') and t not in by: by[t]=sp['stat']
            st=by.get('season') if (by.get('season') or {}).get('gamesPitched',0) else by.get('career')
            if not st or (st.get('gamesPitched') or 0)<5: continue
            k=' '.join(w for w in norm(p['fullName']).split() if w not in ('jr','sr','ii','iii'))
            out.setdefault(k,[]).append('SP' if (st.get('gamesStarted') or 0)*2>=(st.get('gamesPitched') or 1) else 'RP')
    return out

def lookup_ids(names,ids):
    """MLB ids for players who are off the 40-man (released / outrighted free agents)."""
    import urllib.parse
    out={}
    for n in names:
        k=norm(n)
        if k in ids: continue
        try:
            d=get('https://statsapi.mlb.com/api/v1/people/search?sportIds=1&names='+urllib.parse.quote(n))
            for p in d.get('people',[]):
                if norm(p['fullName'])==k: out[k]=p['id']; break
        except Exception: pass
    return out
