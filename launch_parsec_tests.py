import os
import sys
from uuid import UUID
from itertools import starmap
from itertools import product
import multiprocessing as mp

from gem5art.artifact import Artifact
from gem5art.run import gem5Run

packer = Artifact.registerArtifact(
    command = '''wget https://releases.hashicorp.com/packer/1.4.3/packer_1.4.3_linux_amd64.zip;
    unzip packer_1.4.3_linux_amd64.zip;
    ''',
    typ = 'binary',
    name = 'packer',
    path =  'disk-image/packer',
    cwd = 'disk-image',
    documentation = 'Program to build disk images. Downloaded sometime in August 2019 from hashicorp.'
)

experiments_repo = Artifact.registerArtifact(
    command = 'git clone https://github.com/darchr/gem5art-experiments.git',
    typ = 'git repo',
    name = 'parsec_tests',
    path =  './',
    cwd = '../',
    documentation = 'Main repo to run PARSEC tests with gem5'
)

parsec_repo = Artifact.registerArtifact(
    command = '''mkdir parsec-benchmark/;
    cd parsec-benchmark;
    git clone https://github.com/bamos/parsec-benchmark.git;''',
    typ = 'git repo',
    name = 'parsec_repo',
    path =  './disk-image/parsec/parsec-benchmark/',
    cwd = './disk-image/',
    documentation = '''Main repo to copy PARSEC source to the disk-image.'''
)

gem5_repo = Artifact.registerArtifact(
    command = '''
        git clone https://gem5.googlesource.com/public/gem5;
        cd gem5;
        git checkout release-staging-v20.0.0.0;
    ''',
    typ = 'git repo',
    name = 'gem5',
    path =  '/home/amartya/Desktop/Code/gem5',
    cwd = './',
    documentation = 'Cloned gem5 from the Google repository using branch release-staging-v20.0.0.0'
)

m5_binary = Artifact.registerArtifact(
    command = 'scons build/x86/out/m5',
    typ = 'binary',
    name = 'm5',
    path =  '/home/amartya/Desktop/Code/gem5/util/m5/build/x86/out/m5',
    cwd = '/home/amartya/Desktop/Code/gem5/util/m5',
    inputs = [gem5_repo,],
    documentation = 'm5 utility'
)

disk_image = Artifact.registerArtifact(
    command = './packer build parsec/parsec.json',
    typ = 'disk image',
    name = 'parsec',
    cwd = 'disk-image',
    path = 'disk-image/parsec/parsec-image/parsec',
    inputs = [packer, experiments_repo, m5_binary, parsec_repo,],
    documentation = 'Disk-image using Ubuntu 18.04 with m5 binary and PARSEC installed.'
)

gem5_binary = Artifact.registerArtifact(
    command = 'scons build/X86/gem5.opt -j12',
    typ = 'gem5 binary',
    name = 'gem5',
    cwd = '/home/amartya/Desktop/Code/gem5/',
    path =  '/home/amartya/Desktop/Code/gem5/build/X86/gem5.opt',
    inputs = [gem5_repo,],
    documentation = 'gem5 binary'
)

linux_repo = Artifact.registerArtifact(
    command = '''git clone --branch v4.19.83 --depth 1 https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git;
    mv linux linux-stable''',
    typ = 'git repo',
    name = 'linux-stable',
    path =  '/home/amartya/Desktop/Code/linux_stable/',
    cwd = '../',
    documentation = 'Linux kernel source code repo'
)

linux_binary = Artifact.registerArtifact(
    name = 'vmlinux-4.19.83',
    typ = 'kernel',
    path = '/home/amartya/Desktop/Code/linux_stable/vmlinux-4.19.83',
    cwd = '/home/amartya/Desktop/Code/linux_stable/',
    command = '''
    cp ../config.4.19.83 .config;
    make -j8;
    cp vmlinux vmlinux-4.19.83;
    ''',
    inputs = [experiments_repo, linux_repo,],
    documentation = "Kernel binary for v4.19.83"
)

# Update sizes and benchmarks based on available inputs
# benchmarks = ['blackscholes', 'bodytrack', 'canneal', 'dedup','facesim', 'ferret', 'fluidanimate', 'freqmine', 'raytrace', 'streamcluster', 'swaptions', 'vips', 'x264']
benchmarks = ['blackscholes']
sizes = ['simsmall']
# cpus = ['kvm', 'timing']
cpus = ['timing']

if __name__ == "__main__":
    def createRun(bench, size, cpu):
        if cpu == 'timing' and size != 'simsmall':
            return 
        return gem5Run.createFSRun(
            'parsec classic memory tests with gem5-20',    
            '/home/amartya/Desktop/Code/gem5/build/X86/gem5.opt',
            'configs-parsec-tests/run_parsec.py',
            f'''results/run_parsec/{bench}/{size}/{cpu}''',
            gem5_binary, gem5_repo, experiments_repo,
            'linux-stable/vmlinux-4.19.83',
            'disk-image/parsec/parsec-image/parsec',
            linux_binary, disk_image,
            cpu, bench, size, '1',
            timeout = 24*60*60 #24 hours
            )
    
    # For the cross product of tests, create a run object.
    runs = starmap(createRun, product(benchmarks, sizes, cpus))
    
    def worker(run):
        run.run()
        json = run.dumpsJson()
        print(json)

    jobs = []

    # For the cross product of tests, create a run object.
    runs = starmap(createRun, product(benchmarks, cpus, cpus))
    # Run all of these experiments in parallel
    for run in runs:
        jobs.append(run)

    with mp.Pool(mp.cpu_count() // 2) as pool:
         pool.map(worker, jobs)
