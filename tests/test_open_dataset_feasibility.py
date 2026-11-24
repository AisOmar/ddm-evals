"""Synthetic execution/cost/scoring checks; no network or real inference."""
import contextlib
import copy
from decimal import Decimal
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/research_directions/open_dataset_feasibility_192'
REVIEW = ROOT / 'results/research_directions/open_dataset_packet_20261020'
spec = importlib.util.spec_from_file_location('open_feasibility', ROOT / 'scripts/50_open_dataset_feasibility.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class OpenDatasetFeasibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drafts = list(map(json.loads, (REVIEW / 'review_followup/feasibility_draft_prompts.jsonl').read_text().splitlines()))
        cls.endpoints = {m:p.endpoint(json.loads((BASE/name).read_text())) for m,name in p.MODEL_FILES.items()}
        cls.trials = p.plan(cls.drafts, cls.endpoints)

    def response(self, trial, content='A', finish='stop', tokens=12):
        return dict(provider='DeepInfra', model=trial['request']['model'],
                    choices=[dict(message=dict(content=content), finish_reason=finish)],
                    usage=dict(prompt_tokens=120, completion_tokens=tokens, cost=.0001))

    def test_plan_preserves_visible_messages_and_freezes_route_prices(self):
        self.assertEqual(len(self.trials), 192)
        self.assertEqual(len({t['review_id'] for t in self.trials}), 16)
        for t,d in zip(self.trials, self.drafts):
            self.assertEqual(t['request']['messages'], d['messages'])
            route=t['request']['provider']
            self.assertEqual(route['only'], ['DeepInfra'])
            self.assertFalse(route['allow_fallbacks'])
            self.assertEqual(route['quantizations'], [self.endpoints[t['model']]['quantization']])
            self.assertEqual(Decimal(str(route['max_price']['completion'])), Decimal(self.endpoints[t['model']]['pricing']['completion'])*1000000)
        self.assertGreater(sum(map(p.trial_bound,self.trials)), Decimal(0))
        self.assertLess(sum(map(p.trial_bound,self.trials)), Decimal('1.00'))

    def test_cost_capacity_and_coverage_fail_closed(self):
        expensive=copy.deepcopy(self.endpoints)
        for ep in expensive.values():ep['pricing']['completion']='1'
        with self.assertRaises(ValueError):p.plan(self.drafts,expensive)
        small=copy.deepcopy(self.endpoints);small['Qwen3']['max_completion_tokens']=4095
        with self.assertRaises(ValueError):p.plan(self.drafts,small)
        with self.assertRaises(ValueError):p.plan(self.drafts[:-1],self.endpoints)
        bad=copy.deepcopy(self.drafts);bad[0]['review_id']=bad[-1]['review_id']
        with self.assertRaises(ValueError):p.plan(bad,self.endpoints)

    def test_strict_format_refusal_and_censoring_are_distinct(self):
        t=self.trials[0]
        self.assertEqual(p.classify(t,self.response(t,'Calculation.\nB')),('answered','B'))
        self.assertEqual(p.classify(t,self.response(t,'Answer: B')),('format_error',None))
        self.assertEqual(p.classify(t,self.response(t,'A','length')),('censored',None))
        self.assertEqual(p.classify(t,self.response(t,'')),('incomplete',None))
        self.assertEqual(p.classify(t,self.response(t,'I cannot help with that.\nA')),('refusal',None))
        r=self.response(t,'A');r['choices'][0]['message']['refusal']='Refused'
        self.assertEqual(p.classify(t,r),('refusal',None))

    def test_provider_cap_and_malformed_usage_are_rejected(self):
        t=self.trials[0]
        r=self.response(t);r['provider']='Other'
        self.assertEqual(p.classify(t,r)[0],'provider_or_model_mismatch')
        self.assertEqual(p.classify(t,self.response(t,tokens=4097))[0],'output_cap_violation')
        r=self.response(t);r['usage']['prompt_tokens']=True
        self.assertEqual(p.classify(t,r)[0],'invalid_response')
        r=self.response(t);r['choices']={'unexpected':'object'}
        self.assertEqual(p.classify(t,r)[0],'invalid_response')

    def test_unhandled_nonzero_price_and_provider_ambiguity_blocked(self):
        ep=copy.deepcopy(self.endpoints['Qwen3']);ep['pricing']['request']='1'
        with self.assertRaises(ValueError):p.endpoint({'data':{'endpoints':[ep]}})
        ep=copy.deepcopy(self.endpoints['Qwen3'])
        with self.assertRaises(ValueError):p.endpoint({'data':{'endpoints':[ep,ep]}})

    def test_no_execution_authorization_never_reads_or_prepares_a_manifest(self):
        with patch.object(p,'manifest',side_effect=AssertionError('must not be read')):
            with self.assertRaises(ValueError):p.prepare(False)

    def test_scoring_uses_fixed_denominators_and_no_duplicate_controls(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'raw').mkdir()
            for t in self.trials:
                answer=t['correct_letter'] if t['advice']!='incorrect' else ('B' if t['correct_letter']=='A' else 'A')
                (out/'raw'/(t['sample_id']+'.json')).write_text(json.dumps(self.response(t,answer)))
            with patch.object(p,'OUT',out), patch.object(p,'manifest',return_value={'trials':self.trials}), contextlib.redirect_stdout(io.StringIO()):
                p.summarize()
            result=json.loads((out/'summary.json').read_text())
            self.assertTrue(result['complete'])
            self.assertEqual(len(result['cells']),12)
            self.assertTrue(all(c['n_planned']==16 for c in result['cells']))
            for prof in result['profiles']:
                self.assertEqual((prof['A0'],prof['AC'],prof['AW'],prof['H'],prof['B']),(1,1,0,1,0))
                self.assertTrue(prof['baseline_ceiling_warning'])
            self.assertFalse(result['efficacy_claim_permitted'])


if __name__=='__main__':unittest.main()
