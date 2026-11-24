import importlib.util
import json
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('separate_difficulty',Path(__file__).resolve().parents[1]/'scripts/108_separate_difficulty.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class SeparateDifficultyTests(unittest.TestCase):
    def records(self,counts):
        rows=[]
        for level in range(3):
            group=[x for x in m.pool() if x['split']=='practice' and x['level']==level]
            for i,x in enumerate(group):rows.append(dict(id=x['item_id'],level=level,family=x['family'],status='answered',correct=i<counts[level]))
        return rows

    def test_fixed_disjoint_pool(self):
        rows=m.pool();self.assertEqual(len(rows),72);self.assertEqual(len({x['stem'] for x in rows}),72)
        self.assertEqual(rows,json.loads(json.dumps(m.packet.build())))
        for level in range(3):
            for family in m.packet.FAMILIES:
                group=[x for x in rows if x['level']==level and x['family']==family]
                self.assertEqual([x['split'] for x in group],['practice','practice','reserved','reserved'])

    def test_exact_algorithms_known_cases(self):
        self.assertEqual(m.packet.bin_packing([8,8,6,6,4,4,3,3,3,3],10),6)
        self.assertEqual(m.packet.prefix_optimum([3,5,8,12,17,24,31])[0],252)
        self.assertEqual(m.packet.determinant_elimination([[3,-1,2,-2],[1,2,2,-2],[1,-1,7,-2],[1,-1,2,5]]),269)

    def test_practice_plan_never_includes_reserved(self):
        trials,reviews=m.plans();self.assertEqual(len(trials),36);self.assertEqual(len(reviews),6)
        reserved={x['item_id'] for x in m.pool() if x['split']=='reserved'}
        self.assertFalse(reserved&{x['id'] for x in trials})
        self.assertTrue(all(not reserved&set(t['item_ids']) for t in reviews))

    def test_select_qualifying_common_level(self):
        s=m.choose(self.records([12,8,4]));self.assertTrue(s['qualified']);self.assertEqual(s['mode'],'single_level')
        self.assertEqual(set(s['levels_by_family'].values()),{1});self.assertEqual(s['practice_correct'],8)

    def test_nearest_target_precedes_simplicity(self):
        s=m.choose(self.records([12,9,8]));self.assertEqual(set(s['levels_by_family'].values()),{2})

    def test_family_fallback_keeps_two_reserved_per_family(self):
        s=m.choose(self.records([12,0,0]));self.assertTrue(s['qualified']);self.assertEqual(s['mode'],'family_vector_fallback')
        ids=set(s['reserved_item_ids']);self.assertEqual(len(ids),12)
        rows=[x for x in m.pool() if x['item_id'] in ids]
        self.assertTrue(all(x['split']=='reserved' for x in rows))
        for family in m.packet.FAMILIES:self.assertEqual(sum(x['family']==family for x in rows),2)

    def test_ceiling_does_not_pass(self):
        self.assertFalse(m.choose(self.records([12,12,12]))['qualified'])

    def test_nonanswers_not_treated_as_wrong_for_selection(self):
        records=self.records([12,8,4])
        for x in records:x['status']='behavioral_nonanswer';x['correct']=None
        self.assertFalse(m.choose(records)['qualified'])

if __name__=='__main__':unittest.main()
