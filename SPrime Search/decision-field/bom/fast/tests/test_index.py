import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'fast')]
from core import CostVector, ObligationSpec, PartSpec, StepPhase
from catalog import PartCatalog
from index import compile_index

def part(pid, provides, requires=(), ins=(), outs=(), cost=None):
    return PartSpec(pid,1,tuple(provides),tuple(requires),tuple(ins),tuple(outs),(),(),(),(),(),CostVector.from_mapping(cost or {'components':1,'memory':0}),(),(),'test')

def obligation():
    return ObligationSpec('o',1,'test',(('worlds',4),),('transition','observe','infer'),(),'cover',(0,),(0,),('obs',),('observe',),'one',(StepPhase.PRE_ACTION,StepPhase.TRANSITION,StepPhase.OBSERVATION),True,'exact',(),('components','memory'))

class IndexTests(unittest.TestCase):
    def build(self, order):
        ps={
          'z':part('z',('observe',),outs=(('o','Observation'),),cost={'components':1,'memory':0}),
          'a':part('a',('transition',),outs=(('w','WorldState'),),cost={'components':2,'memory':0}),
          'm':part('m',('infer',),requires=('transition','observe'),ins=(('o','Observation'),('w','WorldState')),outs=(('k','KnowledgeState'),),cost={'components':1,'memory':1}),
        }
        c=PartCatalog()
        for k in order:c.register(ps[k],lambda:None)
        return compile_index(obligation(),c)
    def test_slots_stable(self):
        i1=self.build('zam'); i2=self.build('maz')
        self.assertEqual(i1.part_keys,i2.part_keys)
        self.assertEqual(i1.part_keys,(('a',1),('m',1),('z',1)))
    def test_masks_and_required(self):
        i=self.build('zam'); m=i.part_slots[('m',1)]
        expected=sum(1<<i.capability_slots[x] for x in ('infer','observe','transition'))
        self.assertEqual(i.required_capability_mask, expected)
        self.assertTrue(i.require_masks[m] & (1<<i.capability_slots['observe']))
        self.assertTrue(i.provide_masks[m] & (1<<i.capability_slots['infer']))
    def test_cost_order(self):
        i=self.build('zam'); a=i.part_slots[('a',1)]
        self.assertEqual(i.cost_dimensions,('components','memory'))
        self.assertEqual(i.cost_tuples[a],(2,0))
    def test_port_adjacency_exact_type(self):
        i=self.build('zam'); a=i.part_slots[('a',1)]; m=i.part_slots[('m',1)]; z=i.part_slots[('z',1)]
        self.assertIn((a,'w',m,'w'),i.port_edges)
        self.assertIn((z,'o',m,'o'),i.port_edges)
        self.assertNotIn((a,'w',m,'o'),i.port_edges)
if __name__=='__main__': unittest.main()
