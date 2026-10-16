import json,re,sys,os,itertools,unicodedata
RAW=sys.argv[1]; OUT=sys.argv[2]; POSF=sys.argv[3]
TEAMS={'Angels':(108,'angels'),'Diamondbacks':(109,'diamondbacks'),'Orioles':(110,'orioles'),'Red_Sox':(111,'red-sox'),'Cubs':(112,'cubs'),'Reds':(113,'reds'),'Guardians':(114,'guardians'),'Rockies':(115,'rockies'),'Tigers':(116,'tigers'),'Astros':(117,'astros'),'Royals':(118,'royals'),'Dodgers':(119,'dodgers'),'Nationals':(120,'nationals'),'Mets':(121,'mets'),'Athletics':(133,'athletics'),'Pirates':(134,'pirates'),'Padres':(135,'padres'),'Mariners':(136,'mariners'),'Giants':(137,'giants'),'Cardinals':(138,'cardinals'),'Rays':(139,'rays'),'Rangers':(140,'rangers'),'Blue_Jays':(141,'blue-jays'),'Twins':(142,'twins'),'Phillies':(143,'phillies'),'Braves':(144,'braves'),'White_Sox':(145,'white-sox'),'Marlins':(146,'marlins'),'Yankees':(147,'yankees'),'Brewers':(158,'brewers')}
def norm(s):
    s=unicodedata.normalize('NFD',s); s=''.join(c for c in s if unicodedata.category(c)!='Mn').lower()
    s=re.sub(r'\b(jr|sr|ii|iii)\b\.?','',s); return ' '.join(re.sub(r'[^a-z ]','',s).split())
POS=json.load(open(POSF))
def posinfo(name):
    r=POS.get(norm(name))
    if not r: return {'emmanuel clase':'RP','steven cruz':'RP','jurickson profar':'LF'}.get(norm(name))
    p=r.get('pos2') or r['pos']; return 'DH' if p=='TWP' else p
def M(v):
    return None if v is None else round(v/1e6,4)
def span_end(c):
    m=re.search(r'\((\d{4})(?:[-–](\d{2,4}))?',c or '')
    if not m: return None
    a=int(m.group(1)); b=m.group(2)
    if not b: return a
    return int(b) if len(b)==4 else (a//100)*100+int(b) if (a//100)*100+int(b)>=a else (a//100+1)*100+int(b)
def lvl(t):
    if t is None: return None
    t=t.upper()
    if t.startswith('PRE-ARB'): return 'Pre'
    m=re.match(r'ARB (\d)$',t)
    return 'ARB '+m.group(1) if m else None
def cdesc(c):
    if not c.get('descriptionSpan'): return c['description'] or ''
    t=f"{c['descriptionYears']}, {c['descriptionTotal']} {c['descriptionSpan']}"
    if c.get('descriptionOptions'): o=c['descriptionOptions']; t+=(o if o.lstrip()[:1] in ',;' else ', '+o)
    n=c.get('descriptionNotes') or ''
    if n: t+=(n if n.lstrip().startswith(';') else '; '+n)
    return t
Y=[2027,2028,2029,2030,2031,2032]
def yr(c,season):
    for y in c['contractYears']:
        if y['Season']==season: return y
def sal(y):  # a displayed salary (float) or None
    if y is None or y['Salary'] is None or y['Type'] in ('FREE AGENT','FREE AGENT (DISPLAYED)','FREE AGENT (NOT DISPLAYED)') or (y['Type'] or '').startswith('FREE AGENT'): return None
    return M(y['Salary'])
out={}; missing=[]
for team,(tid,slug) in TEAMS.items():
    j27=json.load(open(f'{RAW}/{slug}-2027.json'))['data']; j26=json.load(open(f'{RAW}/{slug}-2026.json'))['data']
    C=j27['dataContract']
    names27={c['contractSummary']['playerName'] for c in C if c['contractSummary']['payrollType']!='not40man'}
    lab26={}
    for c in j26['dataContract']:
        if c['contractSummary']['payrollType']=='not40man': continue
        y=yr(c,2027); lab26[c['contractSummary']['playerName']]=(y['Type'] if y else None)
    pot={}; othrows=[]
    for key,sh in (('dataOtherPayments','Other Payments'),('dataOtherPaymentsLuxuryTax','Other Luxury Tax Payments')):
        by={}
        for r in j27[key]:
            if r['Season'] in Y and r['PaymentAmount'] not in (None,0): by.setdefault(r['PaymentDescription'],{})[r['Season']]=M(r['PaymentAmount'])
        for desc,vals in by.items():
            m=re.search(r'potential buyout of (.+)$',desc)
            if m:
                for y,v in vals.items(): pot.setdefault(m.group(1).strip(),[]).append((y,v))
                continue
            othrows.append((desc,vals,sh))
    g=[];ap=[]
    for c in C:
        s=c['contractSummary']; pt=s['payrollType']; n=s['playerName']
        if pt=='gauranteed':
            cs=cdesc(c); aav=None
            for yy in Y:
                yv=yr(c,yy)
                if yv and yv['AAV'] is not None and sal(yv) is not None: aav=M(yv['AAV']); break
            if aav is None: aav=M(s['AAV'])
            E=span_end(cs); pos=posinfo(n)
            if pos is None: missing.append((team,n))
            it={'n':n,'ps':pos or '','a':s['age'],'c':cs,'v':aav}
            b={};sched={}
            for yy in Y:
                v=sal(yr(c,yy))
                if v is not None:
                    sched[yy]=v
                    if E is None or yy<=E: b[yy]=aav
            it['b']=b
            for (oy,bo) in pot.get(n,[]):
                if (E is None or oy>E) and isinstance(sched.get(oy),float):
                    it['o']={'y':oy,'s':sched[oy],'bo':bo}
            it['s']=sched
            g.append(it)
        elif pt in('arbeligible','arbineligible'):
            pos=posinfo(n)
            if pos is None: missing.append((team,n))
            y0=yr(c,2027); L={}
            raw0=lab26.get(n)
            l0=lvl(raw0)
            if l0 and raw0.upper().startswith('ARB'): L[2027]=l0
            elif raw0 and raw0.upper().startswith('PRE'): L[2027]='Pre'
            v0=y0['ArbSalaryProjection'] if y0 and y0['ArbSalaryProjection'] is not None else (y0['Salary'] if y0 else None)
            hasv=v0 is not None
            if 2027 not in L: L[2027]='ARB ?' if hasv else 'Pre'
            for yy in Y[1:]:
                yv=yr(c,yy)
                if yv and yv['Type'] and not yv['Type'].upper().startswith('FREE'):
                    l=lvl(yv['Type'])
                    if l: L[yy]=l
            it={'n':n,'ps':pos or '','a':s['age'],'l':{str(k):v for k,v in L.items()}}
            if hasv: it['b']={2027:M(v0)}
            ap.append(it)
    pend=[]
    for c in j26['dataContract']:
        s=c['contractSummary']; n=s['playerName']
        if s['payrollType']=='not40man' or n in names27: continue
        y=yr(c,2027)
        if y and (y['Type'] or '').startswith('FREE AGENT'):
            y26=yr(c,2026)
            pend.append({'n':n,'ps':posinfo(n) or '','a':s['age'],'s':M(y26['Salary']) if y26 and y26['Salary'] is not None else None,'c':cdesc(c)})
    o={x['Season']:x for x in j27['dataOverall']}
    def row(f): return [round((M(o[y][f]) if y in o and o[y][f] is not None else 0) or 0,4) for y in Y]
    ltp={}
    ltp['AAVs for players with guaranteed contracts (does not include players no longer on 40-man roster)']=[row('TotalGuaranteedAAV')]
    ltp['Salaries for players eligible for arbitration']=[row('TotalArbitration')]
    ltp['AAVs for players with guaranteed contracts no longer on the 40-man roster']=[row('TotalNoLongerOnRoster')]
    ltp['Earned incentives and escalators']=[row('TotalReachedIncentives')]
    ltp['Sum of Other Payments (does not include potential buyouts)']=[row('TotalOtherPayments')]
    ltp['Estimated salaries for players not yet eligible for arbitration and other players with non-guaranteed contracts']=[row('estOtherPreArb')]
    ltp['Estimated salaries for 40-man roster players in minor leagues']=[row('est40ManMinor')]
    ltp['Estimated player benefits to be paid']=[row('estPlayerBenefits')]
    ltp['Payment into $50M pre-arbitration bonus pool']=[row('estPreArbBonusPool')]
    ltp['Estimated Luxury Tax Payroll']=[row('estLuxuryTaxPayroll')]
    # option / opt-out gap analysis (same as the xlsx pipeline)
    gl=ltp[[k for k in ltp if k.startswith('AAVs for players with guaranteed contracts (')][0]][0]
    unfit=[]
    for i,yy in enumerate(Y):
        mine=sum(float(x['b'].get(yy,0)) for x in g); diff=round(mine-gl[i],3)
        if diff<0.01: continue
        cands=[x for x in g if yy in x['b']]; found=None
        for r in range(1,4):
            for cc in itertools.combinations(cands,r):
                if abs(sum(float(x['b'][yy]) for x in cc)-diff)<0.011: found=cc;break
            if found:break
        if not found: unfit.append((yy,diff)); continue
        for x in found: x.setdefault('ox',[]).append(yy)
    for x in g:
        if 'ox' in x:
            ys=sorted(x['ox'])
            for yy in ys: x['b'].pop(yy,None)
            cl=x['c'].lower(); kind='mutual' if 'mutual' in cl and 'player option' not in cl else 'player'
            bo=0
            for (oy,amt) in pot.get(x['n'],[]):
                if oy in ys: bo=amt; break
            x['o']={'y':int(ys[0]),'ys':[int(v) for v in ys],'s':x['v'],'bo':bo,'k':kind}
        elif 'o' in x:
            cl=x['c'].lower()
            x['o']['k']='mutual' if 'mutual' in cl and 'club option' not in cl else ('player' if 'player option' in cl and 'club option' not in cl else 'club')
    if unfit: print('UNFIT',team,unfit)
    out[str(tid)]={'team':team,'g':g,'ap':ap,'pend':pend,'oth':[(d,{str(k):v for k,v in vs.items()},sh) for d,vs,sh in othrows],'ltp':ltp}
for k,t in out.items():
    for it in t['g']:
        for f in ('b','s'): it[f]={str(a):b for a,b in it[f].items()}
        if 'ox' in it: del it['ox']
    for it in t['ap']:
        if 'b' in it: it['b']={str(a):b for a,b in it['b'].items()}
json.dump(out,open(OUT,'w'),ensure_ascii=False)
print('teams',len(out),'missing pos',len(missing),missing[:20])
