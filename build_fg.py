# Builds data/fg.json from the raw FanGraphs payroll pages in data/fg/raw/.
#   python3 tools/build_fg.py            (run from the repo root)
import json,os,subprocess,sys,datetime,glob,re
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=HERE; RAW=ROOT+'/data/fg/raw'; TMP=ROOT+'/data/fg/.tmp'
os.makedirs(TMP,exist_ok=True)
subprocess.check_call([sys.executable,'-I',HERE+'/fg2raw.py',RAW,TMP+'/teams_raw.json',HERE+'/pos.json'])
subprocess.check_call([sys.executable,'-I',HERE+'/emit_fg.py',HERE,TMP+'/teams_raw.json',ROOT+'/index.html',TMP+'/team_sim.json'])
sys.path.insert(0,HERE); import lg
src=open(HERE+'/fg2raw.py').read(); i=src.index('TEAMS='); j=src.index('\n',i)
ns={}; exec(src[i:j],ns); TEAMS=ns['TEAMS']
league=lg.league(RAW,[(t,v[1]) for t,v in TEAMS.items()])
last={}
for t,(tid,slug) in TEAMS.items():
    d=json.load(open(f'{RAW}/{slug}-2026.json'))['data']
    o=[x for x in d['dataOverall'] if x['Season']==2026]
    if o and o[0].get('estLuxuryTaxPayroll'): last[t.replace('_',' ')]=round(o[0]['estLuxuryTaxPayroll']/1e6,2)
sim=json.load(open(TMP+'/team_sim.json'))
# Spotrac-verified corrections where FanGraphs' trade-cash treatment differs (Arenado: ARI pays $5M/$6M, COL still carries $5M in 2027)
def adjust(sim):
    for tid,t in sim.items():
        if t.get('nick')=='Diamondbacks':
            for g in t['g']:
                if g['n']=='Nolan Arenado' and g['b'].get('2027')==21.0:
                    g['b']['2027']=15.0; t['adj']={'note':'Arenado at $6M: his $15M salary less the $9M the Cardinals pay him directly, per Spotrac','d':{'2027':-6.0}}
        if t.get('nick')=='Rockies' and not any('Arenado' in o['n'] for o in t['oth']):
            t['oth'].append({'n':'Nolan Arenado retained salary (per Spotrac)','b':{'2027':5.0}}); t['adj']={'note':'includes $5M still owed on Arenado, per Spotrac','d':{'2027':5.0}}
adjust(sim)
assert len(sim)==29 and len(league)>600 and len(last)==30, (len(sim),len(league),len(last))
# 40-man players FanGraphs doesn't list + team corrections from the live 40-man rosters (keeps the last good copy if MLB's API is down)
extra=None; poshist=None
try:
    import extra40
    tids={t.replace('_',' '):v[0] for t,v in TEAMS.items()}; tids['Yankees']=147
    extra,live,ids=extra40.build(tids,ROOT+'/index.html',league,sim)
    try:
        fa=json.loads(re.search(r'const FA_TRACKER = (\[.*?\]);\n',open(ROOT+'/index.html',encoding='utf-8').read(),re.S).group(1))
        ids.update(extra40.lookup_ids([x['n'] for x in fa],ids)); poshist=extra40.poshist(ids)
    except Exception as e: print('poshist skipped:',e)
    for r in league:
        n=extra40.norm(r['n'])
        if r.get('k')!='f' and n in live and live[n]!=r['t']: r['t']=live[n]
except Exception as e:
    print('extra40 skipped:',e)
    try: extra=json.load(open(ROOT+'/fg.json')).get('extra40')
    except Exception: extra=None
if not poshist:
    try: poshist=json.load(open(ROOT+'/fg.json')).get('poshist')
    except Exception: poshist=None
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
OUTF=ROOT+'/fg.json'
if os.path.exists(OUTF):   # keep the old timestamp when nothing changed, so a quiet day makes no commit
    try:
        old=json.load(open(OUTF))
        if all(old.get(k)==v for k,v in (('teamSim',sim),('leagueDb',league),('lastYear',last),('extra40',extra or []),('poshist',poshist or {}))): stamp=old.get('updated',stamp)
    except Exception: pass
out={'updated':stamp,'teamSim':sim,'leagueDb':league,'lastYear':last,'extra40':extra or [],'poshist':poshist or {}}
json.dump(out,open(ROOT+'/fg.json','w'),ensure_ascii=False,separators=(',',':'))
import shutil; shutil.rmtree(TMP)
print('wrote fg.json',os.path.getsize(ROOT+'/fg.json'),'bytes;',len(sim),'teams',len(league),'players')
