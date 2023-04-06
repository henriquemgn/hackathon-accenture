from eventfactory import Detection, PipelineStep


class ClassFilter(PipelineStep):
    def __init__(self, classes: dict) -> None:
        self.classes = classes.values()

    def process(self, detection: Detection) -> Detection:
        predictions = filter(self._filter_classes, detection["predictions"])

        detection["predictions"] = list(predictions)

        return detection

    def _filter_classes(self, prediction) -> None:
        return True if prediction["classId"] in self.classes else False
