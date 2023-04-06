from typing import List
from eventfactory import Detection, PipelineStep
from shapely import geometry
from shapely.geometry import polygon


class RegionOfInterest(PipelineStep):
    def __init__(self, region: List) -> None:
        self._region = region

    def process(self, detection: Detection) -> Detection:
        predictions = filter(self.__pred_is_inside_region,
                             detection["predictions"])

        detection['predictions'] = list(predictions)

        return detection

    def __pred_is_inside_region(self, prediction):
        """
        Checks whether a given prediction is inside the ROI.

        This verification is intended to be used when detection people, as
        we consider the medium point of the base of the predicted bbox to be
        their feet.
        """
        bbox_coord = prediction['boundingBox']['coordinates']

        bbox_x_min = min([point['x'] for point in bbox_coord])
        bbox_x_max = max([point['x'] for point in bbox_coord])
        bbox_y_max = max([point['y'] for point in bbox_coord])

        x_mean = (bbox_x_min + bbox_x_max) // 2
        person_foot = geometry.Point(x_mean, bbox_y_max)

        polygon_points = [(point['x'], point['y']) for point in self._region]
        region_polygon = polygon.Polygon(polygon_points)

        return region_polygon.contains(person_foot)
