import json,re,unicodedata,collections
import sys
HERE=sys.argv[1]; RAWF=sys.argv[2]; INDEX=sys.argv[3]; OUTF=sys.argv[4]
raw=json.load(open(RAWF))
Y=['2027','2028','2029','2030','2031','2032']
def norm(x):
    x=unicodedata.normalize('NFD',x); x=''.join(c for c in x if unicodedata.category(c)!='Mn').lower()
    x=re.sub(r'\b(jr|sr|ii|iii)\b\.?','',x); return ' '.join(re.sub(r'[^a-z ]','',x).split())
s=open(INDEX,encoding='utf8').read()
tr=json.loads(re.search(r'const FA_TRACKER = (\[.*?\]);\n',s,re.S).group(1))
ab={'LAA':108,'AZ':109,'ARI':109,'BAL':110,'BOS':111,'CHC':112,'CIN':113,'CLE':114,'COL':115,'DET':116,'HOU':117,'KC':118,'KCR':118,'LAD':119,'WSH':120,'WSN':120,'NYM':121,'ATH':133,'PIT':134,'SD':135,'SDP':135,'SEA':136,'SF':137,'SFG':137,'STL':138,'TB':139,'TBR':139,'TEX':140,'TOR':141,'MIN':142,'PHI':143,'ATL':144,'CWS':145,'CHW':145,'MIA':146,'NYY':147,'MIL':158}
def num(v): return round(v,4) if isinstance(v,(int,float)) else v
out={}
for tid,d in raw.items():
    if tid=='147': continue
    t={'nick':d['team'].replace('_',' ')}
    ltp=d['ltp']
    last=[v for k,v in ltp.items() if k.startswith('Estimated Luxury')][0][0]
    t['fg']={Y[i]:last[i] for i in range(6) if last[i]}
    t['g']=[]
    for x in d['g']:
        it={'n':x['n'],'ps':x['ps'],'a':x['a'],'c':x['c'],'b':{k:x['v'] for k,x2 in [(0,0)] for k in []}}
        it['b']={str(k):v for k,v in x['b'].items()}
        if 'o' in x: it['o']=x['o']
        t['g'].append(it)
    t['ap']=[{k:v for k,v in x.items()} for x in d['ap']]
    oth=[]
    for desc,vals,sh in d['oth']:
        if 'buyout' in desc.lower(): continue
        oth.append({'n':re.sub(r'\s*\(credited.*|\s*\(AAV of money.*','',desc),'b':vals})
    for key,label in [('AAVs for players with guaranteed contracts no longer on the 40-man roster','Guaranteed AAVs of players no longer on the 40-man'),('Earned incentives and escalators','Earned incentives & escalators')]:
        v=ltp.get(key,[[0]*6])[0]
        vals={Y[i]:v[i] for i in range(6) if v[i]}
        if vals: oth.append({'n':label,'b':vals})
    t['oth']=oth
    names27={norm(x['n']) for x in d['g']}|{norm(x['n']) for x in d['ap']}
    pend=[{'n':p['n'],'ps':p['ps'],'a':p['a'],'s':p['s'] if isinstance(p['s'],(int,float)) else 0} for p in d['pend']]
    have={norm(p['n']) for p in pend}
    for r in tr:
        if ab.get(r['o'])==int(tid) and r['l']!='F' and norm(r['n']) not in have and norm(r['n']) not in names27:
            pend.append({'n':r['n'],'ps':r['p'].split('/')[0],'a':r['a'],'s':0})
    qo=json.load(open(HERE+'/qo.json')); 
    for p in pend:
        r=[x for x in qo.get(f"{tid}|{p['n']}",[]) if not x.startswith('?')]
        if r: p['q']='; '.join(r)
    t['prior']=json.load(open(HERE+'/prior.json'))[tid]
    t['pend']=pend
    out[tid]=t
json.dump(out,open(OUTF,'w'),ensure_ascii=False,separators=(',',':'))

