from ovos_utils.log import LOG
from ovos_plugin_manager.templates.intents import IntentExtractor, IntentPriority, IntentDeterminationStrategy, RegexEntityDefinition, EntityDefinition

from palavreado import IntentContainer, IntentCreator


class PalavreadoExtractor(IntentExtractor):
    def __init__(self, config=None,
                 strategy=IntentDeterminationStrategy.SEGMENT_REMAINDER,
                 priority=IntentPriority.MEDIUM_LOW,
                 segmenter=None):
        super().__init__(config, strategy=strategy,
                         priority=priority, segmenter=segmenter)

        self.intent_builders = {}
        self.engine = IntentContainer()

    def register_keyword_intent(self, intent_name,
                                keywords=None,
                                optional=None,
                                at_least_one=None,
                                excluded=None,
                                lang=None):
        if not keywords:
            keywords = keywords or [intent_name]
            self.register_entity(intent_name, keywords)
        optional = optional or []
        excluded = excluded or []
        at_least_one = at_least_one or []
        super().register_keyword_intent(intent_name, keywords, optional, at_least_one, excluded, lang)

        # structure intent
        intent = IntentCreator(intent_name)
        for kw in keywords:
            intent.require(kw, [])
        for kw in optional:
            intent.optionally(kw, [])
        self.intent_builders[intent_name] = intent
        return intent

    def calc_intent(self, utterance, min_conf=0.5, lang=None):
        # update intent definitions with newly registered entity samples
        for intent_name, intent in self.intent_builders.items():
            for kw, samples in [(e.name, e.patterns) for e in self.registered_entities
                                if isinstance(e, RegexEntityDefinition)]:
                if kw in intent.required or kw in intent.optional:
                    intent.regexes[kw] = samples
            for kw, samples in [(e.name, e.samples) for e in self.registered_entities
                                if isinstance(e, EntityDefinition)]:
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
        return None
