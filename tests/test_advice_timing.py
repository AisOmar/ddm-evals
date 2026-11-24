import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('advice_timing',Path(__file__).resolve().parents[1]/'scripts/106_advice_timing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class AdviceTimingTests(unittest.TestCase):
    def test_exact_packet_rebuild(self):
        rows=m.packet.build()
        self.assertEqual([x['answer'] for x in rows],['6','243','656','8','42','68'])
        self.assertEqual(m.c.load(m.OUT/'fresh_author_packet.json'),json.loads(json.dumps(rows)))

    def test_unique_calls_and_shared_controls(self):
        first,second,arms,reviews=m.plan()
        self.assertEqual((len(first),len(second),len(arms),len(reviews)),(18,30,54,2))
        self.assertEqual(len({x['id'] for x in first+second}),48)
        for item in m.packet.build():
            uid=item['item_id']
            before=next(x for x in arms if x['item_id']==uid and x['arm']=='advice_before' and x['advice']=='none')
            after=next(x for x in arms if x['item_id']==uid and x['arm']=='advice_after' and x['advice']=='none')
            self.assertEqual(before['source_id'],after['source_id'])
            late=[x for x in second if x['item_id']==uid and x['timing']=='late']
            self.assertEqual({x['dependency'] for x in late},{uid+'_first_none'})

    def test_late_advice_absent_from_initial_context(self):
        for item in m.packet.build():
            for advice in ('correct','wrong'):
                req=m.second_request(item,'late',advice,'A')
                self.assertNotIn('Recommendation:',req['messages'][0]['content'])
                self.assertIn('Recommendation:',req['messages'][2]['content'])
                self.assertEqual(req['messages'][1],{'role':'assistant','content':'{"answer":"A"}'})

    def test_early_advice_present_once_and_checks_matched(self):
        item=m.packet.build()[0]
        for advice in ('correct','wrong'):
            early=m.second_request(item,'early',advice,'B');late=m.second_request(item,'late',advice,'B')
            self.assertIn('Recommendation:',early['messages'][0]['content'])
            self.assertEqual(early['messages'][2]['content'],m.CHECK)
            self.assertTrue(late['messages'][2]['content'].endswith(m.CHECK))
            self.assertEqual(early['messages'][1],late['messages'][1])

    def test_no_advice_transcripts_identical(self):
        for answer in ('A','B'):
            item=m.packet.build()[0]
            self.assertEqual(m.second_request(item,'early','none',answer),m.second_request(item,'late','none',answer))

    def test_all_arms_have_six_per_cell(self):
        arms=m.plan()[2]
        for arm in m.ARMS:
            for advice in m.CELLS:self.assertEqual(sum(x['arm']==arm and x['advice']==advice for x in arms),6)

    def test_zero_opportunities_are_not_zero_rate(self):
        pairs=[({'correct':True},{'correct':True,'status':'answered'})]
        d=m.transition_summary(pairs)
        self.assertIsNone(d['correction_rate']);self.assertIsNone(d['correction_bounds'])
        self.assertEqual(d['corruption_rate'],0)

    def test_unknown_transitions_get_bounds(self):
        pairs=[({'correct':False},{'correct':None,'status':'behavioral_nonanswer'}),({'correct':True},{'correct':None,'status':'behavioral_nonanswer'})]
        d=m.transition_summary(pairs)
        self.assertIsNone(d['correction_rate']);self.assertIsNone(d['corruption_rate'])
        self.assertEqual(d['correction_bounds'],[0,1]);self.assertEqual(d['corruption_bounds'],[0,1])

if __name__=='__main__':unittest.main()
