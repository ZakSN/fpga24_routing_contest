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

	def manipulator(self):
		manipulator = ConfigurationManipulator()
		manipulator.add_parameter(FloatParameter('ww', 0, 1))
		manipulator.add_parameter(FloatParameter('ipcf', 0.1, 10.0))
		manipulator.add_parameter(FloatParameter('pcm', 1, 10.0))
		manipulator.add_parameter(FloatParameter('hcf', 0.1, 10.0))
		return manipulator

	def compile(self, cfg, id):
		infra = os.path.join('..','fpga24_routing_contest')
		logdir  = os.path.join('..','opentuner','tuneroute_logs')
		cfg_vals = [str(x) for x in [cfg['ww'], cfg['ipcf'], cfg['pcm'], cfg['hcf']]]
		cfg_args = ' '.join(cfg_vals)
		cfg_txt =  '_'.join(cfg_vals)
		logfiles = []
		for bmark in ['logicnets_jscl', 'vtr_mcml']:
			routed = os.path.join(logdir, bmark+"_tuneroute_"+cfg_txt+".phys")
			logfile = os.path.join(logdir, bmark+"_tuneroute_"+cfg_txt+".phys.log")
			rwroute_cmd = "cd "+infra+" && \
				       /usr/bin/time java -cp `cat java-classpath.txt` \
				       com.xilinx.fpga24_routing_contest.TuneRouterPhysNetlist \
				       "+bmark+"_unrouted.phys \
				       "+routed+" \
				       "+cfg_args+" \
				       > "+logfile
			out=self.call_program(rwroute_cmd)
			print(out)
			logfiles.append(logfile)
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
