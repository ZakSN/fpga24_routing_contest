import opentuner
from opentuner import ConfigurationManipulator
from opentuner import FloatParameter
from opentuner import MeasurementInterface
from opentuner import Result

import os

class RWRouteTuner(MeasurementInterface):
	def get_nodes_popped(self, logfile):
		with open(logfile) as lf:
			for line in lf:
				if "Nodes popped:" in line:
					return float(line.split()[-1])
		return float('inf') # TODO fix this

	def manipulator(self):
		manipulator = ConfigurationManipulator()

		#manipulator.add_parameter(FloatParameter('ww', 0, 1))
		#manipulator.add_parameter(FloatParameter('ipcf', 0.1, 10.0))
		#manipulator.add_parameter(FloatParameter('pcm', 1, 10.0))
		#manipulator.add_parameter(FloatParameter('hcf', 0.1, 10.0))

		lower = 0.75
		upper = 1.25
		manipulator.add_parameter(FloatParameter('ww', lower*0.8, upper*0.8))
		manipulator.add_parameter(FloatParameter('ipcf', lower*0.5, upper*0.5))
		manipulator.add_parameter(FloatParameter('pcm', lower*2, upper*2))
		manipulator.add_parameter(FloatParameter('hcf', lower*1, upper*1))
		return manipulator

	def compile(self, cfg, id):
		bmarks = ["logicnets_jscl",
		          "boom_med_pb",
			  "vtr_mcml",
			  "rosetta_fd",
			  "corundum_25g",
			  "finn_radioml"]

		cfg_txt = '_'.join([str(x) for x in [cfg['ww'], cfg['ipcf'], cfg['pcm'], cfg['hcf']]])

		logdir  = os.path.join('tuneroute_logs')
		logfiles = [os.path.join(logdir, bmark+"_tuneroute_"+cfg_txt+".phys.log") for bmark in bmarks]

		rwroute_cmd = ["make", "-j8",
		               "APPTAINER_NETWORK=none",
			       "ROUTER=tuneroute_"+cfg_txt,
			       "BENCHMARKS="+' '.join(bmarks),
			       "WW="+str(cfg['ww']),
			       "IPCF="+str(cfg['ipcf']),
			       "PCM="+str(cfg['pcm']),
			       "HCF="+str(cfg['hcf'])]

		print(' '.join(rwroute_cmd))
		out=self.call_program(rwroute_cmd, cwd='..', limit=6000)
		print(out)
		return logfiles

	def run_precompiled(self, desired_resutl, input, limit, compile_result, id):
		popped = 0.0
		for logfile in compile_result:
			popped = popped + self.get_nodes_popped(logfile)
		return Result(time=popped)

	def compile_and_run(self, desired_result, input, limit):
		cfg = desired_result.configuration.data
		compile_result = self.compile(cfg, 0)
		return self.run_precompiled(desired_result, input, limit, compile_result, 0)

	def save_final_config(self, configuration):
		"""called at the end of tuning"""
		cfg_file = "rwroute_final_config"
		print("Best flags written to "+cfg_file+".{json,cmd}")
		self.manipulator().save_to_file(configuration.data, cfg_file+'.json')

if __name__ == '__main__':
	argparser = opentuner.default_argparser()
	RWRouteTuner.main(argparser.parse_args())
