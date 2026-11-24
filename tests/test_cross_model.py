"""Statistical invariants and collection safeguards; no API calls."""
import importlib.util
import contextlib
import io
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cross=module('cross','28_cross_model.py')
follow=module('follow','29_wording_followup.py')


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d,_=cross.load()

    def test_repeats_do_not_create_independent_questions(self):
        a=cross.estimate(self.d,1000,4)
        doubled=pd.concat([self.d,self.d],ignore_index=True)
        b=cross.estimate(doubled,1000,4)
        self.assertEqual(a['n_questions'],b['n_questions'])
        for p,q in zip(a['pairs'],b['pairs']):
            self.assertAlmostEqual(p['estimate'],q['estimate'],12)
            self.assertAlmostEqual(p['risk_lo'],q['risk_lo'],12)
            # CR1's N/K correction changes slightly; duplicated repeats must not
            # produce the sqrt(2) precision gain of independent trial inference.
            self.assertGreater(q['se']/p['se'],.99)

    def test_cluster_covariance_matches_independent_derivation(self):
        # The log-odds slope influence for a question is the derivative
        # of logit(high mean)-logit(low mean), directly from cell proportions.
        a=cross.estimate(self.d,1000,4)
        z=self.d[self.d.outcome=='answered'].copy()
        z['y']=z.followed.astype(float)
        qids=sorted(self.d.qid.unique())
        influences=[]
        for model in ['R1','Qwen3']:
            parts=[]
            for cell in ['p55','p95']:
                rows=z[(z.model==model)&(z.cell==cell)]
                p=rows.y.mean()
                residual=(rows.y-p).groupby(rows.qid).sum().reindex(qids,fill_value=0)
                parts.append(residual.to_numpy()/(len(rows)*p*(1-p)))
            influences.append((parts[1]-parts[0])/cross.GAP)
        u=influences[0]-influences[1]
        n=len(z)
        se=np.sqrt((u@u)*(100/99)*((n-1)/(n-9)))
        self.assertAlmostEqual(se,a['pairs'][0]['se'],12)

    def test_nonanswers_are_not_coded_as_resistance(self):
        a=cross.estimate(self.d,1000,4)
        rate=next(r for r in a['rates'] if r['model']=='gpt-oss' and r['cell']=='p55')
        self.assertEqual(rate['n'],197)
        self.assertAlmostEqual(rate['followed'],33/197)
        self.assertEqual(cross.holm([.03,.001,.02]).tolist(),[.04,.003,.04])


class CollectionTests(unittest.TestCase):
    def test_retry_after_numeric_date_and_malformed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'sample.attempt1.json'
            p.write_text('{}')
            os.utime(p,(100,100))
            self.assertEqual(follow.retry_due(p,60),160)
            s=p.with_suffix('.retry_after')
            s.write_text('600')
            self.assertEqual(follow.retry_due(p,60),700)
            s.write_text('Thu, 01 Jan 1970 00:20:00 GMT')
            self.assertEqual(follow.retry_due(p,60),1200)
            s.write_text('unparseable')
            self.assertEqual(follow.retry_due(p,60),1000)

    def test_generated_curl_configuration_parses_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            (out/'raw').mkdir()
            (out/'requests').mkdir()
            t=dict(sample_id='mock',request=dict(model='qwen/qwen3-32b',messages=[dict(role='user',content='A or B?')]))
            (out/'requests/mock.json').write_text(json.dumps(t['request']))
            (out/'budget_preflight.json').write_text(json.dumps(dict(key_allowance_check_passed=True,planned_calls=1,operations_sha256='fake',rate_limit_amendment_sha256='fake',account_balance_remaining=5,endpoint_prices={'qwen/qwen3-32b':dict(prompt='0.00000008',completion='0.00000028')})))
            for attempt in range(1,4):
                (out/f'raw/mock.attempt{attempt}.json').write_text(json.dumps(dict(error=dict(code=429))))
            output=io.StringIO()
            with patch.object(follow,'OUT',out),patch.object(follow,'read_manifest',return_value=dict(trials=[t])),patch.object(follow,'sha',return_value='fake'),patch('dotenv.dotenv_values',return_value=dict(OPENROUTER_API_KEY='test-key')),contextlib.redirect_stdout(output):
                follow.prepare(False,300)
                self.assertNotIn('Private configuration:',output.getvalue())
                self.assertIn('cooling down',output.getvalue())
                for p in (out/'raw').glob('*.json'):
                    old=p.stat().st_mtime-901
                    os.utime(p,(old,old))
                output.seek(0)
                output.truncate(0)
                follow.prepare(False,300)
            line=next(s for s in output.getvalue().splitlines() if s.startswith('Private configuration: '))
            config=Path(line.split(': ',1)[1])
            try:
                self.assertEqual(config.stat().st_mode & 0o777,0o600)
                # --version parses the preceding configuration and exits before
                # transfers. Catches unsupported options without making calls.
                r=subprocess.run(['curl','--config',str(config),'--version'],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertIn('Connection: close',config.read_text())
                self.assertIn('mock.attempt4.json',config.read_text())
            finally:
                config.unlink()

    def test_refusal_and_bare_answer_behavior(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            trials=[]
            for i,text in enumerate(['I’m sorry, I can’t help with that.','A','']):
                sid=f'test{i}'
                trials.append(dict(sample_id=sid,qid=f'q{i}',model='R1',wording='frequency',cell='p55',rate=.55,target='B',hint_letter='A'))
            def response(t):
                i=int(t['sample_id'][-1])
                text=['I’m sorry, I can’t help with that.','A',''][i]
                return out/(t['sample_id']+'.json'),dict(provider='DeepInfra',choices=[dict(message=dict(content=text),finish_reason='stop')],usage=dict(completion_tokens=1,cost=.001))
            with patch.object(follow,'OUT',out),patch.object(follow,'read_manifest',return_value=dict(trials=trials)),patch.object(follow,'response',side_effect=response),patch.object(follow,'sha',return_value='fake'):
                d,status=follow.parse()
            self.assertEqual(d.outcome.tolist(),['refusal','answered','incomplete'])
            self.assertTrue(pd.isna(d.iloc[0].chosen))
            self.assertTrue(d.iloc[1].followed)
            self.assertTrue(status['complete'])

    def test_incomplete_collection_blocks_analysis(self):
        with patch.object(follow,'parse',return_value=(pd.DataFrame(),dict(complete=False))):
            with self.assertRaisesRegex(ValueError,'Incomplete collection'):
                follow.analyze()

    def test_response_validation_and_no_duplicate_success(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            (out/'raw').mkdir()
            t=dict(sample_id='q1',request=dict(model='qwen/qwen3-32b'))
            good=dict(provider='DeepInfra',model='qwen/qwen3-32b',choices=[dict(message=dict(content='A'))],usage=dict(completion_tokens=1))
            p=out/'raw/q1.attempt1.json'
            p.write_text(json.dumps(dict(error=dict(code=429))))
            with patch.object(follow,'OUT',out):
                self.assertEqual(follow.response(t),(None,None))
                p.write_text(json.dumps(good))
                self.assertIsNotNone(follow.response(t)[1])
                t['request']['provider']=dict(order=['DekaLLM'],allow_fallbacks=False)
                with self.assertRaisesRegex(ValueError,'Unexpected provider'):
                    follow.response(t)
                good['provider']='DekaLLM'
                p.write_text(json.dumps(good))
                self.assertIsNotNone(follow.response(t)[1])
                (out/'raw/q1.attempt2.json').write_text(json.dumps(good))
                with self.assertRaisesRegex(ValueError,'Duplicate valid'):
                    follow.response(t)

    def test_full_followup_analysis_with_paired_synthetic_data(self):
        rng=np.random.default_rng(91)
        rows=[]
        for q in range(100):
            for model in follow.MODELS:
                for word in ['control']+list(follow.WORDS):
                    for cell in ['control'] if word=='control' else ['p55','p95']:
                        p=.15+({'R1':.3,'Qwen3':0.,'gpt-oss':.1}[model] if cell=='p95' else 0)
                        rows.append(dict(qid=f'q{q}',model=model,wording=word,cell=cell,
                                         sample_id=f'{q}-{model}-{word}-{cell}',outcome='answered',
                                         followed=bool(rng.random()<p),cost=.001))
        d=pd.DataFrame(rows)
        with tempfile.TemporaryDirectory() as td:
            with patch.object(follow,'OUT',Path(td)),patch.object(follow,'parse',return_value=(d,dict(complete=True))),patch.object(follow,'read_manifest',return_value=dict(reused={})),patch.object(follow,'sha',return_value='fake'),contextlib.redirect_stdout(io.StringIO()):
                follow.analyze()
            result=json.loads((Path(td)/'analysis.json').read_text())
            self.assertEqual(result['primary']['n_questions'],100)
            pair=result['primary']['pairs'][0]
            self.assertGreater(pair['estimate'],.15)
            manual=[]
            for model in ['R1','Qwen3']:
                means=d[(d.model==model)&d.wording.isin(['frequency','probability'])].groupby(['wording','cell']).followed.mean()
                manual.append(np.mean([means[w,'p95']-means[w,'p55'] for w in ['frequency','probability']]))
            self.assertAlmostEqual(pair['estimate'],manual[0]-manual[1],12)
            self.assertEqual(len(result['wording_vs_reference']),6)


if __name__=='__main__':
    unittest.main()
