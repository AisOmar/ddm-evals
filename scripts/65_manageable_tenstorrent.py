"""Explicit pre-execution deployment amendment after inactive Qwen preflight."""
import argparse
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('manageable_base',ROOT/'scripts/63_manageable_collect.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.a.ROUTES['Qwen3']=('Tenstorrent','tenstorrent/fp8','fp8')
r.EXTRA_INPUTS=[Path(__file__),ROOT/'docs/MANAGEABLE_DEPLOYMENT_AMENDMENT.md',
    r.BASE/'gpt_endpoint_selection.json',r.BASE/'qwen_endpoint_selection.json']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=tuple(r.N),required=True)
    parser.add_argument('--stage',choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'),required=True)
    parser.add_argument('--execute-authorized',action='store_true');parser.add_argument('--curl-exit',type=int);parser.add_argument('--http-status',type=int)
    args=parser.parse_args();r.configure(args.phase)
    if args.stage=='prepare':r.prepare(args.execute_authorized)
    elif args.stage=='finish':
        if args.curl_exit is None or args.http_status is None:parser.error('Need curl exit and HTTP status')
        r.finish(args.curl_exit,args.http_status)
    else:{'preflight-config':r.c.preflight_config,'freeze':r.freeze,'status':r.status,'refresh-config':r.b.refresh_config,'refresh':r.b.refresh}[args.stage]()
