"""Word lists for the rule-based parser. Small on purpose: unknown words are never guessed into attributes."""


def _s(text: str) -> frozenset:
    return frozenset(text.split())


COLORS = _s("red blue green yellow orange purple pink black white gray grey brown golden gold silver teal cyan "
            "magenta violet beige turquoise crimson scarlet navy maroon indigo ivory lavender emerald")
SHADE_WORDS = _s("dark light bright pale deep")
SIZES = _s("small large big tiny huge giant little tall short enormous massive miniature tiny long wide narrow")
MATERIALS = _s("wooden metal metallic glass stone plastic leather paper steel iron brass copper ceramic cotton "
               "woolen golden-brass marble concrete brick rubber velvet silk")
OTHER_ADJ = _s("old new young ancient broken shiny fluffy furry happy sad sleepy angry smiling friendly cute ugly "
               "beautiful lovely clean dirty rusty wet dry hot cold warm cool soft hard smooth rough empty full "
               "tired strong weak fat thin heavy colorful colourful dark bright pale lonely cozy quiet loud "
               "fresh ripe mysterious futuristic modern classic elegant fancy simple tiny wild tame spooky "
               "glowing sparkling transparent striped spotted nice good cool great amazing pretty weird strange awesome")
ADVERBS = _s("very really extremely quite highly super so too slightly almost just only also")
DETERMINERS = _s("a an the this that these those each every another")
POSSESSIVE_DETS = _s("his her its their my your our")
DROP_PRONOUNS = _s("me us you")
COMMAND_VERBS = _s("draw generate create make show paint render imagine depict illustrate produce give design")
PRONOUNS = _s("it they them he she him her we")
VAGUE_NOUNS = _s("thing things stuff something anything everything someone somebody anyone object objects item items")

# NOTE: relation-ish prepositions live in RELATIONS below; these are tokens that only separate noun phrases.
BOUNDARY_WORDS = _s("for during until like as than if while when where who which that is are was were be been being "
                    "has have had will can then there here but yet")
CONNECTORS = _s("and or &")
NEGATORS = _s("no not never without")

NUMBER_WORDS = {"one": 1, "single": 1, "lone": 1, "solitary": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "both": 2,
                "twin": 2, "triple": 3}

# (phrase tokens) -> (count, kind, label). count None = unknown amount.
QUANTIFIERS = {
    ("a", "couple", "of"): (2, "approximate"), ("couple", "of"): (2, "approximate"),
    ("a", "pair", "of"): (2, "exact"), ("pair", "of"): (2, "exact"),
    ("a", "trio", "of"): (3, "exact"), ("a", "dozen"): (12, "exact"), ("dozen",): (12, "exact"),
    ("half", "a", "dozen"): (6, "exact"), ("dozens", "of"): (None, "approximate"),
    ("hundreds", "of"): (None, "approximate"), ("thousands", "of"): (None, "approximate"),
    ("a", "few"): (None, "approximate"), ("few",): (None, "approximate"),
    ("several",): (None, "approximate"), ("many",): (None, "approximate"), ("some",): (None, "approximate"),
    ("numerous",): (None, "approximate"), ("multiple",): (None, "approximate"),
    ("various",): (None, "approximate"), ("lots", "of"): (None, "approximate"),
    ("a", "lot", "of"): (None, "approximate"),
}
for _w in "group flock herd pack pile stack bunch crowd row swarm cluster collection school set line".split():
    QUANTIFIERS[("a", _w, "of")] = (None, "approximate")
    QUANTIFIERS[(_w, "of")] = (None, "approximate")

# --- lighting / time of day -------------------------------------------------------------------
LIGHTING = {
    ("golden", "hour"): "golden hour", ("blue", "hour"): "blue hour", ("sunset",): "sunset",
    ("sunrise",): "sunrise", ("dusk",): "dusk", ("dawn",): "dawn", ("twilight",): "twilight",
    ("moonlight",): "moonlight", ("moonlit",): "moonlit", ("candlelight",): "candlelight",
    ("candlelit",): "candlelit", ("neon", "lights"): "neon lights", ("neon", "light"): "neon light",
    ("neon",): "neon", ("backlit",): "backlit", ("sunlight",): "sunlight", ("daylight",): "daylight",
    ("soft", "lighting"): "soft lighting", ("soft", "light"): "soft light",
    ("dramatic", "lighting"): "dramatic lighting", ("dramatic", "light"): "dramatic light",
    ("studio", "lighting"): "studio lighting", ("harsh", "lighting"): "harsh lighting",
    ("natural", "light"): "natural light", ("natural", "lighting"): "natural lighting",
    ("warm", "light"): "warm light", ("warm", "lighting"): "warm lighting",
    ("rim", "light"): "rim light", ("rim", "lighting"): "rim lighting",
    ("volumetric", "lighting"): "volumetric lighting", ("volumetric", "light"): "volumetric light",
    ("low", "light"): "low light", ("nighttime",): "nighttime", ("midnight",): "midnight",
}
LIGHT_QUALITY_WORDS = _s("soft warm dim bright harsh natural dramatic cold gentle low studio rim volumetric ambient diffuse golden cool")
TIME_OF_DAY = _s("night morning evening afternoon noon")  # only counted after a preposition (see parser)
LIGHT_LEAD_PREPS = _s("at in during under by with before after until")

# --- environment ------------------------------------------------------------------------------
WEATHER_ADJ = _s("foggy misty rainy snowy stormy cloudy sunny windy overcast hazy")
WEATHER_NOUNS = _s("fog mist rain snow storm thunderstorm blizzard haze")
SETTING_WORDS = _s("underwater outdoors outdoor indoors indoor")
ENV_PLACES = _s("forest woods jungle desert beach ocean sea city town village street alley kitchen bedroom "
                "bathroom room garden park field meadow lake river pond valley cave space sky farm countryside "
                "library office classroom market harbor harbour hills swamp tundra savanna canyon restaurant "
                "cafe airport stadium playground reef wasteland mountains")
ENV_PLACES_MULTI = {("living", "room"): "living room", ("outer", "space"): "outer space",
                    ("coral", "reef"): "coral reef"}
PLACE_PREPS_CONSUMED_BY_ENV = _s("in at on inside within across amid")

# --- style ------------------------------------------------------------------------------------
STYLE_PHRASES = {
    ("oil", "painting"): "oil painting", ("pencil", "drawing"): "pencil drawing",
    ("pencil", "sketch"): "pencil sketch", ("pixel", "art"): "pixel art", ("digital", "art"): "digital art",
    ("digital", "painting"): "digital painting", ("3d", "render"): "3d render", ("low", "poly"): "low poly",
    ("comic", "book"): "comic book", ("line", "art"): "line art", ("concept", "art"): "concept art",
    ("ink", "drawing"): "ink drawing", ("flat", "design"): "flat design", ("art", "deco"): "art deco",
    ("pop", "art"): "pop art", ("hyper", "realistic"): "hyper realistic",
    ("water", "color"): "watercolor", ("black", "and", "white"): "black and white",
}
STYLE_WORDS = _s("watercolor watercolour photorealistic photo-realistic realistic hyperrealistic cartoon anime "
                 "manga cinematic minimalist vintage retro surreal abstract impressionist impressionism "
                 "cyberpunk steampunk fantasy noir illustration isometric monochrome grayscale charcoal sketch "
                 "photograph photography")
SOFT_STYLE_WORDS = _s("vintage retro abstract realistic fantasy minimalist cartoon sketch charcoal")  # may be adjectives
MEDIUM_OF = _s("photo photograph painting drawing sketch portrait illustration render rendering poster")
NEUTRAL_FRAMING_OF = _s("picture image scene view")

# --- frame positions ("in the background", "on the left") --------------------------------------
FRAME_WORDS = {"background": "background", "foreground": "foreground", "middle": "center", "center": "center",
               "centre": "center", "distance": "background", "corner": "corner"}

# --- relations: token sequence -> (canonical, kind, spatial) --------------------------------------
# kind "spatial": always a relation; "place": relation unless the object is an environment noun;
# "unsupported": recorded as an ambiguity, never as a relation.
RELATIONS = {
    ("beside",): ("beside", "spatial"), ("next", "to"): ("beside", "spatial"),
    ("alongside",): ("beside", "spatial"), ("adjacent", "to"): ("beside", "spatial"),
    ("by", "the", "side", "of"): ("beside", "spatial"),
    ("near",): ("near", "spatial"), ("close", "to"): ("near", "spatial"), ("by",): ("near", "spatial"),
    ("behind",): ("behind", "spatial"), ("in", "back", "of"): ("behind", "spatial"),
    ("in", "front", "of"): ("in_front_of", "spatial"),
    ("above",): ("above", "spatial"), ("over",): ("above", "spatial"),
    ("on", "top", "of"): ("on", "spatial"), ("atop",): ("on", "spatial"),
    ("below",): ("below", "spatial"), ("beneath",): ("below", "spatial"),
    ("underneath",): ("below", "spatial"), ("under",): ("below", "spatial"),
    ("to", "the", "left", "of"): ("left_of", "spatial"), ("on", "the", "left", "of"): ("left_of", "spatial"),
    ("on", "the", "left", "side", "of"): ("left_of", "spatial"), ("left", "of"): ("left_of", "spatial"),
    ("to", "the", "right", "of"): ("right_of", "spatial"), ("on", "the", "right", "of"): ("right_of", "spatial"),
    ("on", "the", "right", "side", "of"): ("right_of", "spatial"), ("right", "of"): ("right_of", "spatial"),
    ("inside", "of"): ("inside", "place"), ("inside",): ("inside", "place"), ("within",): ("inside", "place"),
    ("in",): ("inside", "place"), ("on",): ("on", "place"), ("at",): ("at", "place"),
    ("with",): ("with", "with"),
    ("between",): ("between", "unsupported"), ("among",): ("among", "unsupported"),
    ("amid",): ("amid", "unsupported"), ("around",): ("around", "unsupported"),
    ("through",): ("through", "unsupported"), ("across",): ("across", "unsupported"),
    ("along",): ("along", "unsupported"), ("against",): ("against", "unsupported"),
    ("toward",): ("toward", "unsupported"), ("towards",): ("towards", "unsupported"),
    ("into",): ("into", "unsupported"), ("onto",): ("onto", "unsupported"),
    ("outside",): ("outside", "unsupported"), ("opposite",): ("opposite", "unsupported"),
    ("beyond",): ("beyond", "unsupported"), ("from",): ("from", "unsupported"),
}
NEG_PREPS = _s("without")

# --- verbs / participles that must not be read as nouns -------------------------------------------
ACTION_VERBS = _s("sits stands holds rides wears eats jumps runs walks swims sleeps flies floats hovers rests waits "
                  "drinks reads dances sings smiles chases pulls pushes throws catches drives looks stares leans "
                  "plays sat stood held rode wore ate jumped ran walked swam slept flew floated hovered rested "
                  "chased carries carried lies lay")
ING_NOUNS = _s("building ceiling painting drawing king ring wing string spring evening morning clothing bedding "
               "sibling darling pudding icing railing stocking earring viking sling swing thing something nothing "
               "anything everything lightning wedding meeting setting parking being wedding ping")

# --- nouns -------------------------------------------------------------------------------------
KNOWN_NOUNS = _s("""
cat dog bird horse cow sheep pig duck chicken rabbit fox wolf bear lion tiger elephant giraffe monkey panda
deer fish shark whale dolphin turtle frog snake lizard butterfly bee spider owl eagle parrot penguin mouse
robot submarine ship boat car truck bus train plane airplane helicopter bicycle bike motorcycle rocket spaceship
house castle tower bridge barn cabin tent lighthouse windmill church temple door window wall fence gate
tree flower rose sunflower bush leaf grass mountain rock stone hill island cloud sun moon star planet
table chair sofa couch bed lamp desk shelf book cup mug bottle bowl plate jar vase clock mirror
umbrella hat shoe boot bag backpack ball balloon kite flag guitar piano drum violin camera phone computer
laptop television apple banana orange cake pizza bread cheese coffee tea fruit
man woman boy girl child baby person people king queen knight wizard pirate astronaut soldier doctor chef
dragon unicorn ghost monster alien angel fairy mermaid castle sword shield crown treasure chest key
statue fountain bench path road sign light lantern candle fire campfire smoke
teddy bear traffic light fire truck coffee cup tea cup hot air balloon street lamp
""")
COMPOUND_NOUNS = {("teddy", "bear"), ("traffic", "light"), ("fire", "truck"), ("coffee", "cup"), ("tea", "cup"),
                  ("hot", "air", "balloon"), ("street", "lamp"), ("police", "car"), ("school", "bus"),
                  ("ice", "cream"), ("tennis", "ball"), ("space", "ship"), ("light", "house"),
                  ("sea", "horse"), ("coffee", "shop")}
MASS_NOUNS = _s("water grass sand smoke fire food hair mud dust ice fog mist rain snow air music light "
                "fruit coffee tea bread cheese")
SINGULAR_S = _s("glass grass bus dress class boss moss cross lens gas canvas atlas cactus octopus walrus circus "
                "chorus virus bonus campus citrus mattress princess actress compass fortress address news series "
                "species iris tennis chess bias gas lotus hippopotamus")
PLURAL_ONLY = _s("jeans scissors pants trousers glasses sunglasses shorts goggles binoculars")
UNCHANGED_PLURAL = _s("sheep fish deer moose bison swine")
IRREGULAR_PLURALS = {"men": "man", "women": "woman", "children": "child", "people": "person", "mice": "mouse",
                     "geese": "goose", "feet": "foot", "teeth": "tooth", "wolves": "wolf", "leaves": "leaf",
                     "knives": "knife", "shelves": "shelf", "lives": "life", "halves": "half", "loaves": "loaf",
                     "oxen": "ox", "buses": "bus", "dice": "die", "geese": "goose", "lice": "louse"}
IES_KEEP_IE = _s("cookie movie zombie pie tie selfie rookie smoothie hoodie brownie genie collie calorie")
OES_SINGULAR = _s("potato tomato hero volcano echo mosquito tornado")
