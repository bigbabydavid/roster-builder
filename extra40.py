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
    extra=[]; live={}
    for nick,tid in teams.items():
        r=get(f'https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=40Man&hydrate=person')['roster']
        if len(r)<35: raise RuntimeError('short roster '+nick)
        for x in r:
            p=x['person']; k=norm(p['fullName']); live.setdefault(k,nick)
            if k not in known:
                extra.append([p['fullName'],nick,p.get('currentAge'),x['position']['abbreviation'],x['status']['code'],p['id']])
    return sorted(extra,key=lambda r:(r[1],r[0])),live
