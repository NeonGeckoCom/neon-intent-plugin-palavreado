from ovos_plugin_manager.intents import IntentExtractor, IntentPriority, IntentDeterminationStrategy, IntentMatch, EntityDefinition, RegexEntityDefinition
from palavreado import IntentContainer, IntentCreator


class PalavreadoExtractor(IntentExtractor):
    def __init__(self, config=None,
                 strategy=IntentDeterminationStrategy.SEGMENT_REMAINDER,
                 priority=IntentPriority.KEYWORDS_LOW,
                 segmenter=None):
        super().__init__(config, strategy=strategy,
                         priority=priority, segmenter=segmenter)
        self.engines = {}  # lang: IntentContainer

    def _get_engine(self, lang=None):
        lang = lang or self.lang
        if lang not in self.engines:
            self.engines[lang] = IntentContainer()
        return self.engines[lang]

    def calc_intent(self, utterance, min_conf=0.0, lang=None, session=None):
        lang = lang or self.lang
        engine = self._get_engine(lang)

        # update intents with registered entity samples
        for intent in self.registered_intents:
            if intent.lang != lang:
                continue
            intent = IntentCreator(intent.name)
            for entity in self.registered_entities:
                if entity.lang != lang:
                    continue
                if isinstance(entity, RegexEntityDefinition):
                    intent.regexes[entity.name] = entity.samples
                elif entity.name in intent.required:
                    intent.required[entity.name] = entity.samples
                elif entity.name in intent.optional:
                    intent.optional[entity.name] = entity.samples
            engine.add_intent(intent)

        intent = engine.calc_intent(utterance)
        if intent.get("conf") > 0:
            intent["intent_engine"] = "palavreado"
            intent["intent_type"] = intent.pop("name")

            skill_id = self.get_intent_skill_id(intent["intent_type"])
            return IntentMatch(intent_service=intent["intent_engine"],
                               intent_type=intent["intent_type"],
                               intent_data=intent,
                               confidence=intent["conf"],
                               skill_id=skill_id)

        return None
