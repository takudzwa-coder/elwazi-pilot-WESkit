import os
import shutil
import subprocess

def teardown_module(module):
    path = os.path.join(os.getcwd(), "tests/wf3/")
    shutil.rmtree(path + "work")
    shutil.rmtree(path + ".nextflow")
    os.remove(path + "hello_world.txt")
    os.remove(path + ".nextflow.log")

def test_execute_nextflow_workflow():
    subprocess.run(["nextflow", "helloworld.nf"], cwd=os.path.join(os.getcwd(), "tests/wf3/"))
    assert os.path.isfile(os.path.join(os.getcwd(), "tests/wf3/hello_world.txt"))
