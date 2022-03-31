from ovos_utils.log import LOG
from ovos_plugin_manager.intents import IntentExtractor, IntentPriority, IntentDeterminationStrategy

from palavreado import IntentContainer, IntentCreator


class PalavreadoExtractor(IntentExtractor):
    def __init__(self, config=None,
                 strategy=IntentDeterminationStrategy.SEGMENT_REMAINDER,
                 priority=IntentPriority.KEYWORDS_LOW,
                 segmenter=None):
        super().__init__(config, strategy=strategy,
                         priority=priority, segmenter=segmenter)

        self.intent_builders = {}
        self.rx_entities = {}
        self.engine = IntentContainer()

    def register_regex_entity(self, entity_name, samples):
        self.rx_entities[entity_name] = samples

    def register_regex_intent(self, intent_name, samples):
        self.register_regex_entity(intent_name + "_rx", samples)
        self.register_intent(intent_name, [intent_name + "_rx"])

    def register_intent(self, intent_name, samples=None,
                        optional_samples=None):
        """
        :param intent_name: intent_name
        :param samples: list of required registered entities (names)
        :param optional_samples: list of optional registered samples (names)
        :return:
        """
        super().register_intent(intent_name, samples)
        samples = samples or []
        optional_samples = optional_samples or []
        # structure intent
        intent = IntentCreator(intent_name)
        for kw in samples:
            intent.require(kw, [])
        for kw in optional_samples:
            intent.optionally(kw, [])
        self.intent_builders[intent_name] = intent
        return intent

    def calc_intent(self, utterance, min_conf=0.0):
        # update intents with registered entity samples
        for intent_name, intent in self.intent_builders.items():
            for kw, samples in self.rx_entities.items():
                if kw in intent.required or kw in intent.optional:
                    intent.regexes[kw] = samples
            for kw, samples in self.registered_entities.items():
                if kw in intent.required:
                    intent.required[kw] = samples
                elif kw in intent.optional:
                    intent.optional[kw] = samples
            self.engine.add_intent(intent)
        intent = self.engine.calc_intent(utterance)
        if intent.get("conf") > 0:
            intent["intent_engine"] = "palavreado"
            intent["intent_type"] = intent.pop("name")
            return intent
        return {"conf": 0, "intent_type": "unknown", "entities": {},
                "utterance": utterance, "utterance_remainder": utterance,
                "intent_engine": "palavreado"}
