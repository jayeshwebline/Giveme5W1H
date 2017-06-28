import logging
import multiprocessing

from extractors import action_extractor, environment_extractor, cause_extractor, method_extractor
from preprocessors.preprocessor_core_nlp import Preprocessor

from combined_scoring.distance_of_candidate import DistanceOfCandidate

class FiveWExtractor:
    """
    The FiveWExtractor bundles all parsing modules.
    """

    log = None
    preprocessor = None
    extractors = []
    

    def __init__(self, preprocessor=None, extractors=None, combinedScorers=None):
        """
        Initializes the given preprocessor and extractors.

        :param extractors: List of Extractors
        :type extractors: [AbsExtractor]
        :param preprocessor: Preprocessor used to prepare the passed documents
        :type preprocessor: Preprocessor
        """

        # first initialize logger
        self.log = logging.getLogger('GiveMe5W')

        if preprocessor:
            self.preprocessor = preprocessor
        else:
            self.preprocessor = Preprocessor('http://localhost:9000')

        # initialize extractors
        if extractors is not None and len(extractors) > 0:
            self.extractors = extractors
        else:
            # the default extractor selection
            self.log.info('No extractors passed, initializing default configuration.')
            self.extractors = [
                action_extractor.ActionExtractor(),
                environment_extractor.EnvironmentExtractor(),
                cause_extractor.CauseExtractor(),
                method_extractor.MethodExtractor()
            ]
            
        if combinedScorers and len(combinedScorers) > 0:
            self.combinedScorers = combinedScorers
        else:
            self.log.info('No combinedScorers passed, initializing default configuration.')
            self.combinedScorers = [
                DistanceOfCandidate( ('What', 'Who'),('How'), 1)
            ]
            
    def parse(self, doc):
        """
        Pass a document to the preprocessor and the extractors

        :param doc: document object to parse
        :type doc: Document

        :return: the processed document
        """
        # preprocess the document
        if not doc.is_preprocessed():
            self.preprocessor.preprocess(doc)
            self.log.debug("Preprocessor: Finished preprocessing: '%s...'" % doc.get_title()[:50])
        else:
            self.log.debug("Preprocessor: Skipped it is already preprocessored: '%s...'" % doc.get_title()[:50])

        # pass the document to the extractors
        threads = []
        for extractor in self.extractors:
            # every document is processed in a new thread
            t = multiprocessing.Process(target=extractor.extract, args=(doc,))
            threads.append(t)
            t.start()

        # wait for the extractors to terminate
        for t in threads:
            t.join()

        # apply combined_scoring
        if self.combinedScorers:
            for combinedScorer in self.combinedScorers:
                combinedScorer.score(doc)
        
        return doc
