import json, pathlib, subprocess, sys, tempfile
HERE=pathlib.Path(__file__).resolve().parent

def run(n,g):
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td)/'x.json'
        subprocess.run([sys.executable,str(HERE/'experiment_a_symmetry.py'),'--n',str(n),'--g',str(g),'--out',str(p)],check=True)
        return json.loads(p.read_text())

def main():
    d=run(3,4)
    assert d['exact_class_preserved'] and d['identity_control']['function_count']==91 and d['certified_symmetry']['candidate_nands']==1106
    h=run(4,5)
    assert h['exact_class_preserved'] and h['identity_control']['function_count']==1243
    assert h['identity_control']['candidate_nands']==301979 and h['certified_symmetry']['candidate_nands']==17346
    assert h['identity_control']['generated_states_excluding_initial']==87880 and h['certified_symmetry']['generated_states_excluding_initial']==4345
    c=json.loads((HERE/'CHECKPOINT.json').read_text())
    assert c['experiment_a']['conclusion']=='GENUINE_CONSTRUCTION_VOLUME_DISCRIMINATOR_NOT_RUNTIME_DOMINANCE'
    assert c['experiment_b']['conclusion']=='NOT_A_TOTAL_COST_DISCRIMINATOR_UNDER_FROZEN_RULE'
    assert c['provenance']['guard_feedback_zip']['published'] is False
    assert c['provenance']['linear_ecs_zip']['published'] is False
    print('PASS pnp decision-field discriminators')
if __name__=='__main__': main()
