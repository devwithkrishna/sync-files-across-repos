import logging
import logging.config
import os

import yaml
from dotenv import load_dotenv


def setup_logging(default_path='logging-conf.yaml', default_level: int = logging.INFO,
				  env_key='LOGGING_CONFIG'):
	"""
	Setup logging configuration
	:param default_path: path to the logging configuration file
	:param default_level: default logging level
	:param env_key: environment variable key for the logging configuration file path
	"""
	load_dotenv()
	path = default_path
	value = os.getenv(env_key, None)
	if value:
		path = value

	if os.path.exists(path):
		with open(path, 'r') as f:
			config = yaml.safe_load(f.read())
		logging.config.dictConfig(config)
	else:
		logging.basicConfig(level=default_level)

	return None
