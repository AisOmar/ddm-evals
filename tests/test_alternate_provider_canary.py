import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('alternate_canary',ROOT/'scripts/58_alternate_provider_canary.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class AlternateProviderTests(unittest.TestCase):
    def endpoint(self):
        return dict(provider_name='DekaLLM',quantization='bf16',status=0,
            supported_parameters=['temperature','max_tokens'],
            pricing=dict(prompt='.00000003',completion='.00000018',input_cache_read='.00000003'))

    def test_cache_cost_is_bounded_by_prompt_rate_and_unknown_charges_rejected(self):
        ep=self.endpoint()
        self.assertEqual(a.endpoint({'data':{'endpoints':[ep]}},'DekaLLM','bf16'),ep)
        for field,value in [('input_cache_read','.1'),('input_cache_write','.1'),('request','.1')]:
            bad=copy.deepcopy(ep);bad['pricing'][field]=value
            with self.assertRaises(ValueError):a.endpoint({'data':{'endpoints':[bad]}},'DekaLLM','bf16')

    def test_real_provider_checked_without_mutating_saved_response(self):
        trial=dict(expected_provider='DekaLLM',correct_letter='A',options={'A':'5','B':'6'},
                   request=dict(model='openai/gpt-oss-120b',max_tokens=512))
        response=dict(provider='DekaLLM',model='openai/gpt-oss-120b',
                      choices=[dict(message=dict(content='A'),finish_reason='stop')],
                      usage=dict(prompt_tokens=50,completion_tokens=10,cost=.00001))
        before=copy.deepcopy(response)
        self.assertTrue(a.result(trial,response,200)['correct'])
        self.assertEqual(response,before)
        response['provider']='DeepInfra'
        self.assertEqual(a.result(trial,response,200)['status'],'provider_or_model_mismatch')

    def test_wrong_quantization_or_duplicate_active_endpoint_rejected(self):
        ep=self.endpoint()
        for rows,quant in [([ep],'fp8'),([ep,copy.deepcopy(ep)],'bf16')]:
            with self.assertRaises(ValueError):a.endpoint({'data':{'endpoints':rows}},'DekaLLM',quant)
