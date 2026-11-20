"""Run after build_fg.py and the transaction-log step.
FanGraphs' payroll pages can lag the transaction tracker by a day, so a player traded yesterday can still sit on his old
club's page. This moves each traded player's contract (or arbitration/pre-arb line) to the club that acquired him,
using the tracker rows in tx.json, and drops a pending free agent from his old club once he has signed elsewhere.
Safe to re-run: a player already on the right club is left alone."""
import json, re, unicodedata
ABBR = {'ARI':'Diamondbacks','ATH':'Athletics','ATL':'Braves','BAL':'Orioles','BOS':'Red Sox','CHC':'Cubs','CHW':'White Sox','CIN':'Reds','CLE':'Guardians','COL':'Rockies','DET':'Tigers','HOU':'Astros','KCR':'Royals','LAA':'Angels','LAD':'Dodgers','MIA':'Marlins','MIL':'Brewers','MIN':'Twins','NYM':'Mets','NYY':'Yankees','PHI':'Phillies','PIT':'Pirates','SDP':'Padres','SEA':'Mariners','SFG':'Giants','STL':'Cardinals','TBR':'Rays','TEX':'Rangers','TOR':'Blue Jays','WSN':'Nationals'}
def norm(s): return re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()).strip()
fg = json.load(open('fg.json')); tx = json.load(open('tx.json'))
T = {v['nick']: v for v in fg['teamSim'].values()}
moved = 0
def find(team, k, name): return next((i for i,p in enumerate(team.get(k,[])) if norm(p['n'])==norm(name)), -1)
for date,team,name,mlbam,cat,detail,change,pos in tx['rows']:
    if date < '2026-10-28' or not detail: continue
    new = T.get(ABBR.get(team,''))
    m = re.match(r'Acquired from (.+?)(?: with | for |$)', detail)
    if m and new:
        old = T.get(m.group(1).strip())
        if old and old is not new and not any(find(new,k,name)>=0 for k in ('g','ap','oth')):
            for k in ('g','ap'):
                i = find(old,k,name)
                if i < 0: continue
                p = old[k].pop(i); new.setdefault(k,[]).append(p)
                if k=='g':
                    for y,v in (p.get('b') or {}).items():
                        if old.get('fg') and old['fg'].get(y) is not None: old['fg'][y] = round(old['fg'][y]-(v or 0),4)
                        new.setdefault('fg',{}); new['fg'][y] = round((new['fg'].get(y) or 0)+(v or 0),4)
                for j in range(len(old.get('oth',[]))-1,-1,-1):   # his signing-bonus / adjustment lines travel with him
                    q = old['oth'][j]
                    if norm(q['n']).startswith(norm(name)+' '):
                        old['oth'].pop(j); new.setdefault('oth',[]).append(q)
                        for y,v in (q.get('b') or {}).items():
                            if old.get('fg') and old['fg'].get(y) is not None: old['fg'][y] = round(old['fg'][y]-(v or 0),4)
                            new.setdefault('fg',{}); new['fg'][y] = round((new['fg'].get(y) or 0)+(v or 0),4)
                for e in fg['leagueDb']:
                    if norm(e['n'])==norm(name) and e['t']==old['nick']: e['t'] = new['nick']
                moved += 1; print('moved', name, old['nick'], '->', new['nick'])
                break
    if re.search(r'non-?tender', detail, re.I) and new:      # non-tendered players come off the club's payroll lines
        for k in ('ap',):
            i = find(new,k,name)
            if i >= 0: new[k].pop(i); moved += 1; print('non-tendered', name, 'off', new['nick'])
    if cat=='FREE AGENT' and detail.startswith('Agreed to') and change!='SUB' and new:
        for t in T.values():
            if t is new: continue
            i = find(t,'pend',name)
            if i >= 0: t['pend'].pop(i); moved += 1; print('signed elsewhere', name, 'off', t['nick'], 'pending list')
json.dump(fg, open('fg.json','w'), separators=(',',':'), ensure_ascii=False)
print('changes', moved)
