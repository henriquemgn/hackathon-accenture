import json
import base64
from typing import Union

from eventfactory.pipeline import (Detection,
                                   EventPipeline,
                                   EventEndedSignal,
                                   EventStartedSignal)
from .roi import RegionOfInterest
from .business_logic import RoIBusinessLogic


class Pipeline(EventPipeline):

    def __init__(self, cfg):
        area_of_interest_b64 = cfg.use_case.area_of_interest
        area_of_interest = json.loads(base64.b64decode(area_of_interest_b64))
        region_coords = area_of_interest["polygon"]["coordinates"]

        self._region_of_interest = RegionOfInterest(region_coords)

        params_b64 = cfg.use_case.params
        params = json.loads(base64.b64decode(params_b64).decode("utf8"))
        min_occurrences = params["minOcurrences"]
        max_outliers = params["maxOutliers"]

        self._business_logic = RoIBusinessLogic(min_occurrences, max_outliers)

    def alerta(self, predictions):

        for i in range(len(predictions)):                           # FOR loop que percorre a lista de predictions 
            classId = predictions[i]['classId']                     # atribui a variavel classId o value do objeto identificado pela IA
            if classId == 'backpack' or classId == 'handbag':       # verifica se o objeto é um objeto 'proibido'
                print(classId + " encontrada! Avise o funcionario") # se for retorna true e printa
                return True
            else:
                return False                                        # se nao retorna false

    def process_detection(self, detection: Detection) -> Union[
                                                        None,
                                                        EventEndedSignal,
                                                        EventStartedSignal]:

        """
            detection retorna um dict com as seguintes keys:
                                                            'frame',
                                                            'url',
                                                            'processedAt',
                                                            'misc' e
                                                            'predictions'

            onde o key predictions é uma lista de dict com as previsões da IA
            e dentro dessa lista de dict há o key 'classId' que tem como value o objeto identificado pela IA
        """

        predictions = detection['predictions']
        self.alerta(predictions)

        detection = self._region_of_interest.process(detection)
        event = self._business_logic.process(detection)

        return event

    