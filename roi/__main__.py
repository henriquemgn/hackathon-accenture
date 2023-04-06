from eventfactory.configuration import cfg
from eventfactory import EventFactory
from .pipeline import Pipeline

lib_config = cfg.library

pipeline = Pipeline(lib_config)

eventFactory = EventFactory(lib_config,
                            None,
                            None,
                            None,
                            pipeline_overwrite=pipeline)

eventFactory.start()

