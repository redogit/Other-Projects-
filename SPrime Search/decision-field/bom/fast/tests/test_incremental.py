import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'fast')]
from core import CostVector,ObligationSpec,PartSpec,StepPhase
from catalog import PartCatalog
from index import compile_index
from incremental import subset_certificate,enumerate_indexed_candidates,IncrementalSearchState

def p(i,prov,req=()):
    return PartSpec(f'p{i}',1,tuple(prov),tuple(req),(),(),(),(),(),(),(),CostVector.from_mapping({'components':1}),(),(),'x')
def o(req):
    return ObligationSpec('o',1,'x',(),tuple(req),(),'cover',(0,),(0,),(),(),'one',(StepPhase.PRE_ACTION,),True,'exact',(),('components',))
class IncrementalTests(unittest.TestCase):
  def test_exact_candidate_masks(self):
    parts=[p(0,('transition',)),p(1,('observe',)),p(2,('infer',),('transition','observe')),p(3,('transition','observe'))]
    c=PartCatalog(); [c.register(x,lambda:None) for x in parts]
    idx=compile_index(o(('transition','observe','infer')),c)
    got=set(enumerate_indexed_candidates(idx).masks)
    exp=set()
    for mask in range(1,1<<len(parts)):
      provided=0; needed=idx.required_capability_mask
      for i in range(len(parts)):
        if mask>>i&1:
          provided |= idx.provide_masks[i]; needed |= idx.require_masks[i]
      if needed & ~provided == 0: exp.add(mask)
    self.assertEqual(got,exp)
  def test_rejection_reasons(self):
    parts=[p(0,('infer',),('transition',)),p(1,('observe',))]
    c=PartCatalog(); [c.register(x,lambda:None) for x in parts]
    idx=compile_index(o(('infer','observe')),c)
    cert=subset_certificate(idx,0b11)
    self.assertFalse(cert.accepted); self.assertEqual(cert.reason,'missing_dependency')
    cert2=subset_certificate(idx,0b10)
    self.assertEqual(cert2.reason,'missing_required_capability')
  def test_active_mask(self):
    parts=[p(0,('transition',)),p(1,('observe',)),p(2,('transition','observe'))]
    c=PartCatalog(); [c.register(x,lambda:None) for x in parts]
    idx=compile_index(o(('transition','observe')),c)
    full=set(enumerate_indexed_candidates(idx).masks)
    restricted=set(enumerate_indexed_candidates(idx,active_part_mask=0b011).masks)
    self.assertTrue(restricted < full)
    self.assertTrue(all((m & ~0b011)==0 for m in restricted))
  def test_cache_dependency_invalidation(self):
    parts=[p(0,('transition',))]
    c=PartCatalog(); c.register(parts[0],lambda:None)
    state=IncrementalSearchState(compile_index(o(('transition',)),c))
    state.put_cache('frontier',('a',),dependencies=('sensor_allowed','budget'))
    state.put_cache('proof',('ok',),dependencies=('geometry',))
    before=state.fingerprint
    invalidated=state.apply_distinction('sensor_allowed',False)
    self.assertEqual(invalidated,('frontier',))
    self.assertNotEqual(before,state.fingerprint)
    self.assertIsNone(state.get_cache('frontier'))
    self.assertEqual(state.get_cache('proof'),('ok',))
if __name__=='__main__': unittest.main()
