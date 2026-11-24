"""Use the frozen original analysis unchanged on the qualified DeepInfra version."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


q=module('qualified_deepinfra_pilot','79_deepinfra_wording_pilot.py')
analysis=module('unchanged_wording_analysis','69_wording_analysis.py')


def analyze():
    q.configure();q.gates()
    analysis.w=q
    analysis.BASE=q.BASE
    analysis.analyze()


if __name__=='__main__':analyze()
