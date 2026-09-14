from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,subprocess,tempfile,shutil
ROOT=Path(__file__).resolve().parent
@dataclass
class CompiledNative:
    path:Path
    tempdir:str
    def cleanup(self): shutil.rmtree(self.tempdir,ignore_errors=True)
def compile_native(source:Path|None=None):
    source=source or ROOT/'native_search.cpp'
    td=tempfile.mkdtemp(prefix='bom-native-'); exe=Path(td)/'native_search'
    subprocess.run(['g++','-O3','-std=c++17',str(source),'-o',str(exe)],check=True,timeout=45,capture_output=True,text=True)
    return CompiledNative(exe,td)
def run_native(task,compiled:CompiledNative,timeout=10):
    n=len(task.provide_masks)
    if n>64: raise ValueError('native kernel supports <=64 parts')
    payload=f"{n} {task.required_mask}\n"+''.join(f"{p} {r}\n" for p,r in zip(task.provide_masks,task.require_masks))
    cp=subprocess.run([str(compiled.path)],input=payload,text=True,capture_output=True,check=True,timeout=timeout)
    obj=json.loads(cp.stdout)
    if set(obj)!= {'count','mask','expansions'}: raise ValueError('native output schema')
    return obj
