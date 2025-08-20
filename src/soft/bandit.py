
from __future__ import annotations
import random, time
from typing import Dict, List, Tuple
from .storage import get_offers_for_segment

class BetaTS:
    """Bandit Beta Thompson Sampling sur reward binaire (conversion). Simplifié.
    On ne persiste pas l'état ici; l'état réel devrait aller en DB. Ici, fallback random.
    """
    def __init__(self):
        self.state: Dict[str, Dict[str, Tuple[int,int]]] = {}  # seg -> offer -> (a,b)

    def pick(self, seg_id: str, offers: List[Tuple[str,str]]) -> Tuple[str,str]:
        if not offers:
            return ("", "")
        # init
        self.state.setdefault(seg_id, {})
        for oid,_ in offers:
            self.state[seg_id].setdefault(oid, (1,1))
        # sample
        samples = []
        for oid,_ in offers:
            a,b = self.state[seg_id][oid]
            samples.append((random.betavariate(a,b), oid))
        samples.sort(reverse=True)
        chosen = samples[0][1]
        url = dict(offers)[chosen]
        return (chosen, url)

    def update(self, seg_id: str, offer_id: str, converted: bool):
        s = self.state.setdefault(seg_id, {})
        a,b = s.get(offer_id, (1,1))
        if converted: a += 1
        else: b += 1
        s[offer_id] = (a,b)

bandit = BetaTS()

def choose_offer(seg_id: str) -> Tuple[str,str]:
    offers = get_offers_for_segment(seg_id)
    oid,url = bandit.pick(seg_id, offers)
    return oid,url
