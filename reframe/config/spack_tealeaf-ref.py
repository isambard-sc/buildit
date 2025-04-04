import os
import reframe as rfm
import reframe.utility as util
import reframe.utility.sanity as sn
from reframe.core.backends import getlauncher
from spack_base import SpackCompileOnlyBase

class TeaLeafRefSpackBuild(SpackCompileOnlyBase):

    defspec = 'tealeaf@master'
    env_spackspec = { 
        'gcc-12': { 'spec': f'{defspec} fflags=-fallow-argument-mismatch' },
        'gcc-13': { 'spec': f'{defspec} fflags=-fallow-argument-mismatch' },
        'gcc-12-macs': { 'spec': f'{defspec} fflags=-fallow-argument-mismatch' },
        'gcc-13-macs': { 'spec': f'{defspec} fflags=-fallow-argument-mismatch' },
    }


# RegressionTest is used so Spack uses existing environment.
# This also uses same spec.
@rfm.simple_test
class TeaLeafRefSpackCheck(rfm.RegressionTest):
    
    tealeafref_binary = fixture(TeaLeafRefSpackBuild, scope='environment')
    fullspackspec = variable(str)

    descr = 'Tealeaf-ref test using Spack'
    build_system = 'Spack'
    valid_systems = ['*']
    valid_prog_environs = ['*']
    
    #num_nodes = parameter([1, 2, 4])
    num_nodes = parameter([1,2,4,8,16])
    num_threads = variable(int, value=1)
    exclusive_access = True
    extra_resources = {
        'memory': {'size': '0'}
    }

    #: The version of the benchmark suite to use.
    #:
    #: :type: :class:`str`
    #: :default: ``'1.0.0'``
    benchmark_version = variable(str, value='1.0.0', loggable=True)

    #: Parameter pack encoding the benchmark information.
    #:
    #: The first element of the tuple refers to the benchmark name,
    #: the second is the energy reference and the third is the
    #: tolerance threshold.
    #:
    #: :type: `Tuple[str, float, int]`
    #: :values:
    benchmark_info = parameter([
        #('tea_bm_1.in', 157.55084183279294, 10),
        #('tea_bm_2.in', 106.27221178646569, 10),
        #('tea_bm_3.in', 99.955877498324000, 10),
        #('tea_bm_4.in', 97.277332050749976, 10),
        ('tea_bm_5.in', 95.462351583362249, 10),
        #('tea_bm_6.in', 95.174738768320850, 10)
    ], fmt=lambda x: x[0], loggable=True)

    executable = 'tea_leaf'
    
    keep_files = ['tea.out']
 
    @run_after('init')
    def prepare_test(self):
        self.__bench, self.__nrg_ref, self.__ts_ref = self.benchmark_info
        self.descr = f'TeaLeaf-ref {self.__bench} benchmark'
        self.prerun_cmds = [
            f'curl -o tea.in https://raw.githubusercontent.com/UK-MAC/TeaLeaf_ref/master/Benchmarks/{self.__bench}',
        ]
    
    @run_after('setup')
    def set_environment(self):
        self.skip_if(
            self.num_nodes > self.current_partition.extras.get('max_nodes',128),
            'exceeded node limit'
        )
        self.build_system.environment = os.path.join(self.tealeafref_binary.stagedir, 'rfm_spack_env')
        self.build_system.specs       = self.tealeafref_binary.build_system.specs
        self.fullspackspec            = ' '.join(self.tealeafref_binary.build_system.specs)
    
    @run_before('run')
    def set_job_size(self):
        proc = self.current_partition.processor
        self.num_tasks_per_node = proc.num_cores
        if self.num_threads:
            #self.num_tasks_per_node = proc.num_cores // self.num_threads
            self.env_vars['OMP_NUM_THREADS'] = self.num_threads
            self.env_vars['OMP_PLACES'] = 'cores'
            self.env_vars['OMP_PROC_BIND'] = 'close'

        self.num_tasks = self.num_nodes * self.num_tasks_per_node

    @loggable
    @property
    def bench_name(self):
        '''The benchmark name.

        :type: :class:`str`
        '''

        return self.__bench

    @property
    def energy_ref(self):
        '''The energy reference value for this benchmark.

        :type: :class:`str`
        '''
        return self.__nrg_ref

    @property
    def timestep_ref(self):
        '''The timestep expected to finish.

        :type: :class:`str`
        '''
        return self.__ts_ref

    @performance_function('s')
    def perf(self):
        return sn.extractsingle(r'Wall clock\s+(?P<perf>\S+)',
                                'tea.out', 'perf', float, item=-1)

    def energy_tealeaf(self):
        return sn.extractsingle(fr'step:\s*{self.__ts_ref}(\s+\S+){{4}}\s+(?P<energy>\S+)',
                                'tea.out', 'energy', float)

    @performance_function('%')
    def obtain_energy_readout(self):
        '''Assert that the obtained energy is met'''
        ke = self.energy_tealeaf()
        qa_diff = 100.0*(ke/self.__nrg_ref)-100.0
        return qa_diff

    @sanity_function
    def assert_complete(self):
        return sn.assert_found(r'Tea is finishing', 'tea.out') 
