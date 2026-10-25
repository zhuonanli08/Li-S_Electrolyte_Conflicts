"""Print indexed original-text passages, without consulting extraction references."""
import argparse, json, re
from step8a_prepare_debug53 import OUT

TOPIC = re.compile(r'electrolyte|solvat|polysul|coulomb|capacit|cycl|Li.?metal|lithium.?metal|LiNO|retention|polariz|overpotential|shuttl|viscos|conductiv|transference|lithium salt|LiTFSI|LiFSI|pouch|loading|thickness|anode|cathode',re.I)
MECH = re.compile(r'due to|because|owing to|attribut|indicat|suggest|demonstrat|reveal|suppress|promot|facilitat|inhibit|mitigat|enhanc|accelerat|consequent|therefore|however|resulting|lead.{0,6}to|conclu',re.I)
NUM = re.compile(r'\d.{0,16}(?:mAh|cycles?|wt|vol|M\b| m\b|mg|μ|µ|mA|%|°|S cm|mS|h\b)|\b(?:prepared|assembled|mixed|dissolv|ratio)\b',re.I)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('ids',nargs='+');ap.add_argument('--kind',choices=['all','mechanism','numbers'],default='all');ap.add_argument('--limit',type=int,default=0);ap.add_argument('--rank',action='store_true');a=ap.parse_args()
    mf={x['id']:x for x in json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))}
    for pid in a.ids:
        print('\n###',pid,mf[pid]['doi'],mf[pid]['title'])
        segs=json.loads((OUT/'sources'/f'{pid}.json').read_text(encoding='utf-8'))
        chosen=[]
        for s in segs:
            t=s['text']
            if not TOPIC.search(t):continue
            if len(t)<70:continue
            # Reference entries are navigational noise, not article evidence.
            if re.match(r'^(?:\[?\d+[\].)]|\([0-9]+\))\s+[A-Z][a-z]+,',t):continue
            keep=MECH.search(t) if a.kind=='mechanism' else NUM.search(t) if a.kind=='numbers' else (NUM.search(t) or MECH.search(t))
            if keep:chosen.append(s)
        if a.rank:
            def score(s):
                t=s['text'];z=0
                if len(t)>1000:return -10
                z+=3*len(re.findall(r'due to|because|owing to|attribut|therefore|consequent|resulting|lead.{0,6}to',t,re.I))
                z+=2*len(re.findall(r'shuttl|parasitic|kinetic|gelation|dendrit|passivat|deplet|consum|solvat',t,re.I))
                z+=len(re.findall(r'suppress|promot|facilitat|inhibit|mitigat|enhanc|accelerat|corros|failure|diffus',t,re.I))
                if re.search(r'\bwe\b|this work|in conclusion|herein',t,re.I):z+=3
                if re.search(r'previous|reported|well.known|it is known|literature',t,re.I):z-=3
                if s['part']=='si':z-=2
                return z
            chosen=sorted(chosen,key=score,reverse=True)
        if a.limit: chosen=chosen[:a.limit]
        print('selected',len(chosen),'total_indexed',len(segs),'selection',a.kind,'limit',a.limit)
        for s in chosen: print(f"[{s['id']} p{s['page']}] {s['text']}")

if __name__=='__main__':main()
