"""Opt-in live integration probe. Uses the owner's installed Muse session."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'service'))
import muse_agent


def verify():
    with tempfile.TemporaryDirectory(prefix='beemuse-live-probe-') as folder:
        base=Path(folder)
        # The index and working directory are separate on purpose.
        library=base/'library';work=base/'project';library.mkdir();work.mkdir()
        html=library/'nexus-probe.html';html.write_text('<title>NexusMCPProbe</title>',encoding='utf-8')
        ident='a'*20
        (library/'catalog.json').write_text(json.dumps({'files':[{
            'id':ident,'name':html.name,'title':'NexusMCPProbe','path':str(html)}]}),encoding='utf-8')
        original=os.environ.get('BEE_LIBRARY_DIR')
        os.environ['BEE_LIBRARY_DIR']=str(library)
        try:
            answer=muse_agent.converse(
                'Prueba de integración autorizada: usa la herramienta MCP search_html para buscar NexusMCPProbe. '
                'Selecciona ese resultado para mostrarlo en la interfaz. Después crea prueba.txt en la carpeta de trabajo '
                'con exactamente BEEMUSE_TOOLS_OK. Usa también la terminal para calcular 17 + 25 e indica el resultado. '
                'No leas otras carpetas ni uses internet.',selected_workspace=work)
        finally:
            if original is None:os.environ.pop('BEE_LIBRARY_DIR',None)
            else:os.environ['BEE_LIBRARY_DIR']=original
        target=work/'prueba.txt'
        tests={'fileCreatedWithExpectedContent':target.is_file() and target.read_text(encoding='utf-8').strip()=='BEEMUSE_TOOLS_OK',
               'indexedSelectionReturned':any(row['id']==ident for row in answer['files']),
               'calculationResultMentioned':'42' in answer['message']}
        return {'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),
                'platform':platform.system(),'model':'Muse Code · Meta',
                'checks':tests,'passed':all(tests.values()),
                'scope':'Synthetic temporary files only. Does not certify OAuth, microphone, other platforms or BeeCode.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Live Muse and MCP probe; consumes requests from your Muse allowance.')
    parser.add_argument('--output',type=Path,default=ROOT/'runtime'/'live-probe.json')
    args=parser.parse_args()
    report=verify();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)
