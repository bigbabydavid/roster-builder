# Builds data/fg.json from the raw FanGraphs payroll pages in data/fg/raw/.
#   python3 tools/build_fg.py            (run from the repo root)
import json,os,subprocess,sys,datetime,glob
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
assert len(sim)==29 and len(league)>600 and len(last)==30, (len(sim),len(league),len(last))
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
OUTF=ROOT+'/fg.json'
if os.path.exists(OUTF):   # keep the old timestamp when nothing changed, so a quiet day makes no commit
    try:
        old=json.load(open(OUTF))
        if all(old.get(k)==v for k,v in (('teamSim',sim),('leagueDb',league),('lastYear',last))): stamp=old.get('updated',stamp)
    except Exception: pass
out={'updated':stamp,'teamSim':sim,'leagueDb':league,'lastYear':last}
json.dump(out,open(ROOT+'/fg.json','w'),ensure_ascii=False,separators=(',',':'))
import shutil; shutil.rmtree(TMP)
print('wrote fg.json',os.path.getsize(ROOT+'/fg.json'),'bytes;',len(sim),'teams',len(league),'players')
