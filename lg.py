import json,re
Y=[2027,2028,2029,2030,2031,2032]
def M(v): return None if v is None else round(v/1e6,4)
def yr(c,s):
    for y in c['contractYears']:
        if y['Season']==s: return y
def league(raw,teams):
    out=[]
    for team,slug in teams:
        d=json.load(open(f'{raw}/{slug}-2027.json'))['data']
        for c in d['dataContract']:
            s=c['contractSummary']; pt=s['payrollType']
            if pt=='not40man': continue
            n=s['playerName']; pid=s['playerId']; pid=int(pid) if pid and str(pid).isdigit() else pid
            rec={'n':n,'t':team.replace('_',' '),'g':round(s['age']) if s['age'] else None,'i':pid}
            ys=[]
            for yy in Y:
                y=yr(c,yy); t=(y['Type'] or '') if y else ''
                if not y or (not t): ys.append(None); continue
                tu=t.upper()
                if tu.startswith('FREE AGENT'): ys.append('FA')
                elif pt=='gauranteed': ys.append(M(y['Salary']) if y['Salary'] is not None else None)
                elif tu.startswith('PRE-ARB'): ys.append('Pre')
                elif tu.startswith('ARB'):
                    m=re.match(r'ARB (\d)',tu)
                    ys.append(('A'+m.group(1)) if m else None)
                else: ys.append(None)
            if pt=='gauranteed':
                # first year may be an option/etc with a salary; xlsx marks FA-in-2027 players as 'f'
                if ys[0]=='FA': rec['k']='f'; rec['c']=cdesc(c); out.append(rec); continue
                v=None
                for yy in Y:
                    yv=yr(c,yy)
                    if yv and yv['AAV'] is not None and yv['Salary'] is not None: v=M(yv['AAV']); break
                rec.update(k='g',c=cdesc(c),v=v if v is not None else M(s['AAV']),y=ys)
            else:
                y0=yr(c,2027); proj=y0['ArbSalaryProjection'] if y0 and y0['ArbSalaryProjection'] is not None else (y0['Salary'] if y0 else None)
                if isinstance(ys[0],str) and ys[0] in('Pre',) and proj is None: rec['k']='p'
                elif proj is not None: rec['k']='a'; rec['m']=M(proj); ys[0]=M(proj)
                else:
                    rec['k']='a'
                    if ys[0] is None: ys[0]='Pre'
                rec['y']=ys
            out.append(rec)
    return out
def cdesc(c):
    if not c.get('descriptionSpan'): return c['description'] or ''
    t=f"{c['descriptionYears']}, {c['descriptionTotal']} {c['descriptionSpan']}"
    if c.get('descriptionOptions'):
        o=c['descriptionOptions']; t+=(o if o.lstrip()[:1] in ',;' else ', '+o)
    n=c.get('descriptionNotes') or ''
    if n: t+=(n if n.lstrip().startswith(';') else '; '+n)
    return t
