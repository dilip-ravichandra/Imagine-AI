"""Deterministic, rule-based prompt analysis. No ML, no network, no LLM.

Pipeline: tokenize -> mark phrase-level items (style, lighting, weather/setting, frame position, relations)
-> split remaining tokens into noun-phrase segments -> parse each segment -> resolve relations.
Anything the rules cannot decide is reported in `ambiguities`; nothing is invented.
"""
import re
from dataclasses import dataclass, field
from typing import Optional

from . import lexicon as L
from .schema import (Ambiguity, Attribute, Complexity, EnvironmentItem, MAX_PROMPT_CHARS, Negation,
                     PromptAnalysis, Relation, SceneObject, Tagged, Validation)

TOKEN_RE = re.compile(r"\w+(?:[-'’]\w+)*|[^\w\s]", re.UNICODE)
_MAX_REL = max(len(k) for k in L.RELATIONS)


@dataclass
class Tok:
    text: str
    low: str
    start: int
    end: int
    used: bool = False

    @property
    def is_word(self) -> bool:
        return bool(re.match(r"\w", self.text))


@dataclass
class Mark:
    kind: str          # REL | FRAME | UNSUP | NEGP | SILENT
    length: int
    data: dict = field(default_factory=dict)


def lemma(word: str) -> tuple[str, Optional[bool]]:
    """(singular, is_plural). is_plural None = cannot tell (sheep, jeans)."""
    w = word
    if w in L.IRREGULAR_PLURALS:
        return L.IRREGULAR_PLURALS[w], True
    if w in L.UNCHANGED_PLURAL or w in L.PLURAL_ONLY:
        return w, None
    if w in L.MASS_NOUNS or w in L.SINGULAR_S or w.endswith(("ss", "us", "is", "ous", "ics")):
        return w, False
    if len(w) > 3 and w.endswith("ies"):
        return (w[:-1] if w[:-1] in L.IES_KEEP_IE else w[:-3] + "y"), True
    if w.endswith(("ches", "shes", "xes", "zes", "sses")):
        return w[:-2], True
    if w.endswith("oes") and w[:-2] in L.OES_SINGULAR:
        return w[:-2], True
    if w.endswith("s") and len(w) > 2:
        return w[:-1], True
    return w, False


def is_action_word(low: str) -> bool:
    if low in L.ACTION_VERBS:
        return True
    return len(low) >= 6 and low.endswith("ing") and low not in L.ING_NOUNS


class _Parser:
    def __init__(self, raw: str):
        self.raw = raw
        self.toks = [Tok(m.group(), m.group().lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(raw)]
        self.marks: dict[int, Mark] = {}
        self.style: list[Tagged] = []
        self.lighting: list[Tagged] = []
        self.env: list[EnvironmentItem] = []
        self.objects: list[SceneObject] = []
        self.relations: list[Relation] = []
        self.negations: list[Negation] = []
        self.amb: list[Ambiguity] = []
        self._o = self._e = self._w = 0

    # ---------------- helpers ----------------
    def _ev(self, a: int, b: int) -> str:
        return self.raw[a:b]

    def _add_amb(self, code: str, detail: str, span=None):
        if not any(a.code == code and a.detail == detail for a in self.amb):
            self.amb.append(Ambiguity(code=code, detail=detail, span=span))

    def _free(self, i: int, n: int) -> bool:
        return i + n <= len(self.toks) and not any(t.used for t in self.toks[i:i + n])

    def _take(self, i: int, n: int, mark: Optional[Mark] = None):
        for t in self.toks[i:i + n]:
            t.used = True
        if mark:
            self.marks[i] = mark

    def _longest(self, i: int, table, maxlen: int):
        for n in range(min(maxlen, len(self.toks) - i), 0, -1):
            key = tuple(t.low for t in self.toks[i:i + n])
            if key in table and self._free(i, n):
                return n, key
        return None

    # ---------------- marking passes ----------------
    def mark_all(self):
        self._mark_medium_of()
        self._mark_style()
        self._mark_lighting()
        self._mark_env_words()
        self._mark_frame()
        self._mark_relations()

    def _mark_medium_of(self):
        T = self.toks
        for i, t in enumerate(T):
            if t.used or t.low not in (L.MEDIUM_OF | L.NEUTRAL_FRAMING_OF):
                continue
            if i + 1 < len(T) and T[i + 1].low == "of" and not T[i + 1].used:
                start = i - 1 if i > 0 and T[i - 1].low in L.DETERMINERS and not T[i - 1].used else i
                if t.low in L.MEDIUM_OF:
                    self.style.append(Tagged(value=t.low, kind="medium", evidence=t.text, span=[t.start, t.end]))
                self._take(start, i + 2 - start, Mark("SILENT", i + 2 - start))

    def _mark_style(self):
        T = self.toks
        # "in the style of <reference>"
        for i in range(len(T) - 1):
            if T[i].low == "style" and T[i + 1].low == "of" and self._free(i, 2):
                start = i - 2 if i >= 2 and T[i - 2].low == "in" and T[i - 1].low == "the" and self._free(i - 2, 2) else i
                j = i + 2
                stop = L.CONNECTORS | L.BOUNDARY_WORDS | {w for k in L.RELATIONS for w in k[:1]}
                while j < len(T) and j < i + 6 and T[j].is_word and T[j].low not in stop and not T[j].used:
                    j += 1
                n = j - start
                if j > i + 2:
                    a, b = T[i + 2].start, T[j - 1].end
                    self.style.append(Tagged(value=self._ev(a, b).lower(), kind="reference",
                                             evidence=self._ev(a, b), span=[a, b]))
                else:
                    self._add_amb("STYLE_REFERENCE_EMPTY", "'style of' is not followed by a named style.",
                                  [T[i].start, T[i + 1].end])
                self._take(start, n, Mark("SILENT", n))
        i = 0
        while i < len(T):
            if T[i].used:
                i += 1
                continue
            hit = self._longest(i, L.STYLE_PHRASES, 3)
            if hit:
                n, key = hit
                a, b = T[i].start, T[i + n - 1].end
                self.style.append(Tagged(value=L.STYLE_PHRASES[key], kind="medium_or_genre",
                                         evidence=self._ev(a, b), span=[a, b]))
            elif T[i].low in L.STYLE_WORDS:
                n = 1
                a, b = T[i].start, T[i].end
                self.style.append(Tagged(value=T[i].low, kind="medium_or_genre", evidence=T[i].text, span=[a, b]))
                nxt = T[i + 1] if i + 1 < len(T) else None
                if (T[i].low in L.SOFT_STYLE_WORDS and nxt and nxt.is_word and not nxt.used
                        and nxt.low not in L.CONNECTORS | L.BOUNDARY_WORDS | L.DETERMINERS
                        and (nxt.low,) not in L.RELATIONS):
                    self._add_amb("STYLE_OR_ATTRIBUTE",
                                  f"'{T[i].text}' could be an art style or a description of '{nxt.text}'.", [a, b])
            else:
                i += 1
                continue
            end = i + n
            if end < len(T) and T[end].low == "of" and not T[end].used:
                n += 1
            self._take(i, n, Mark("SILENT", n))
            i += n

    def _mark_lighting(self):
        T = self.toks
        i = 0
        while i < len(T):
            if T[i].used:
                i += 1
                continue
            q = i
            while q < len(T) and T[q].low in L.LIGHT_QUALITY_WORDS and not T[q].used:
                q += 1
            if q > i and q < len(T) and T[q].low in ("light", "lighting") and not T[q].used:
                a, b = T[i].start, T[q].end
                s0 = i
                if s0 > 0 and T[s0 - 1].low in L.DETERMINERS and not T[s0 - 1].used:
                    s0 -= 1
                if s0 > 0 and T[s0 - 1].low in L.LIGHT_LEAD_PREPS and not T[s0 - 1].used:
                    s0 -= 1
                self.lighting.append(Tagged(value=self._ev(a, b).lower(), kind="light_quality",
                                            evidence=self._ev(a, b), span=[a, b]))
                self._take(s0, q + 1 - s0, Mark("SILENT", q + 1 - s0))
                i = q + 1
                continue
            hit = self._longest(i, L.LIGHTING, 2)
            n, value, kind = 0, None, None
            if hit:
                n, key = hit
                value = L.LIGHTING[key]
                kind = ("time_of_day" if value in ("golden hour", "blue hour", "sunset", "sunrise", "dusk", "dawn",
                                                   "twilight", "nighttime", "midnight")
                        else "light_source" if value in ("moonlight", "moonlit", "candlelight", "candlelit",
                                                         "neon", "neon light", "neon lights", "sunlight", "daylight")
                        else "light_quality")
            start = i
            if hit or T[i].low in L.TIME_OF_DAY:
                s = i
                if s > 0 and T[s - 1].low in L.DETERMINERS and not T[s - 1].used:
                    s -= 1
                if s > 0 and T[s - 1].low in L.LIGHT_LEAD_PREPS and not T[s - 1].used:
                    s -= 1
                    start = s
                    if not hit:  # time-of-day words need a preposition ("at night", "in the morning")
                        n, value, kind = 1, T[i].low, "time_of_day"
                elif not hit:
                    i += 1
                    continue
                if n:
                    a, b = T[i].start, T[i + n - 1].end
                    self.lighting.append(Tagged(value=value, kind=kind, evidence=self._ev(a, b), span=[a, b]))
                    self._take(start, i + n - start, Mark("SILENT", i + n - start))
                    i += n
                    continue
            i += 1

    def _mark_env_words(self):
        for i, t in enumerate(self.toks):
            if t.used:
                continue
            if t.low in L.WEATHER_ADJ or t.low in L.SETTING_WORDS:
                self._w += 1
                cat = "weather" if t.low in L.WEATHER_ADJ else "setting"
                self.env.append(EnvironmentItem(id=f"w{self._w}", name=t.low, category=cat,
                                                evidence=t.text, span=[t.start, t.end]))
                self._take(i, 1, Mark("SILENT", 1))

    def _mark_frame(self):
        T = self.toks
        pos_map = {"left": "left", "right": "right", "top": "top", "bottom": "bottom", "middle": "center",
                   "center": "center", "centre": "center", "background": "background",
                   "foreground": "foreground", "distance": "background", "corner": "corner"}
        for i in range(len(T) - 2):
            if (T[i].low in ("on", "to", "at", "in") and T[i + 1].low == "the" and T[i + 2].low in pos_map
                    and self._free(i, 3)):
                j = i + 3
                if j < len(T) and T[j].low == "side":
                    j += 1
                value = pos_map[T[i + 2].low]
                if j < len(T) and T[j].low == "of":
                    if value in ("left", "right"):
                        continue  # real relation ("to the left of X"): handled by the relation pass
                    self._take(i, j + 1 - i, Mark("UNSUP", j + 1 - i,
                                                  {"phrase": self._ev(T[i].start, T[j].end)}))
                    continue
                self._take(i, j - i, Mark("FRAME", j - i, {"value": value,
                                                           "phrase": self._ev(T[i].start, T[j - 1].end)}))

    def _mark_relations(self):
        T = self.toks
        i = 0
        while i < len(T):
            if T[i].used:
                i += 1
                continue
            if T[i].low in L.NEGATORS:
                self._take(i, 1, Mark("NEGP", 1))
                i += 1
                continue
            hit = self._longest(i, L.RELATIONS, _MAX_REL)
            if hit:
                n, key = hit
                canon, kind = L.RELATIONS[key]
                phrase = self._ev(T[i].start, T[i + n - 1].end)
                self._take(i, n, Mark("REL", n, {"canon": canon, "kind": kind, "phrase": phrase,
                                                 "span": [T[i].start, T[i + n - 1].end], "key": key}))
                i += n
            else:
                i += 1

    # ---------------- segmentation ----------------
    def _is_head_candidate(self, t: Tok) -> bool:
        w = t.low
        return not (w in L.DETERMINERS or w in L.POSSESSIVE_DETS or w in L.ADVERBS or w in L.COLORS
                    or w in L.SHADE_WORDS or w in L.SIZES or w in L.MATERIALS or w in L.OTHER_ADJ
                    or w in L.COMMAND_VERBS or w in L.DROP_PRONOUNS or w in L.NUMBER_WORDS or w.isdigit()
                    or w == "of" or not t.is_word)

    def _elements(self) -> list[dict]:
        T, out, cur = self.toks, [], []

        def flush():
            nonlocal cur
            if cur:
                out.append({"t": "SEG", "toks": cur})
                cur = []

        i = 0
        while i < len(T):
            t = T[i]
            if i in self.marks:
                m = self.marks[i]
                if m.kind == "SILENT":
                    i += m.length
                    continue
                flush()
                out.append({"t": m.kind, **m.data, "start": t.start})
                i += m.length
                continue
            if t.used:
                i += 1
                continue
            if not t.is_word:
                if t.text == ",":
                    flush(); out.append({"t": "CONN", "word": ","})
                elif t.text in ".;!?:":
                    flush(); out.append({"t": "BREAK"})
                elif t.text == "&":
                    flush(); out.append({"t": "CONN", "word": "and"})
            elif t.low in L.CONNECTORS:
                flush(); out.append({"t": "CONN", "word": t.low})
            elif t.low in L.BOUNDARY_WORDS or t.low == "to":
                flush(); out.append({"t": "SEP"})
            elif is_action_word(t.low) and t.low not in L.VAGUE_NOUNS:
                flush(); out.append({"t": "ACTION", "word": t.low, "span": [t.start, t.end]})
            elif (t.low in ("a", "an", "the") and cur and any(self._is_head_candidate(c) for c in cur)
                  and cur[-1].low != "of"):
                flush(); cur.append(t)
            else:
                cur.append(t)
            i += 1
        flush()
        return out

    # ---------------- noun phrase ----------------
    def _parse_np(self, toks: list[Tok]):
        ts = [t for t in toks if t.is_word and t.low not in L.CONNECTORS]
        k = 0
        while k < len(ts) and (ts[k].low in L.COMMAND_VERBS or ts[k].low in L.DROP_PRONOUNS
                               or ts[k].low in L.ADVERBS or ts[k].low == "of"):
            k += 1
        ts = ts[k:]
        if not ts:
            return None
        low = [t.low for t in ts]
        pos, det, count, kind, quant = 0, None, None, None, None
        for n in (3, 2, 1):
            if tuple(low[:n]) in L.QUANTIFIERS:
                count, kind = L.QUANTIFIERS[tuple(low[:n])]
                quant, pos = " ".join(low[:n]), n
                break
        else:
            if low[0] in L.DETERMINERS or low[0] in L.POSSESSIVE_DETS:
                det, pos = low[0], 1
        if pos < len(low) and (low[pos] in L.NUMBER_WORDS or (low[pos].isdigit() and len(low[pos]) <= 4)):
            count = L.NUMBER_WORDS.get(low[pos]) or int(low[pos])
            kind = "exact"
            quant = (quant + " " + low[pos]) if quant else low[pos]
            pos += 1
        rest = ts[pos:]
        attrs: list[Attribute] = []
        cand: list[Tok] = []
        others: list[str] = []
        complement: list[str] = []
        j = 0
        while j < len(rest):
            t, w = rest[j], rest[j].low
            if w == "of":
                complement = [x.low for x in rest[j + 1:] if x.low not in L.DETERMINERS | L.ADVERBS]
                break
            if w in L.DETERMINERS or w in L.POSSESSIVE_DETS or w in L.ADVERBS:
                j += 1
                continue
            if w in L.SHADE_WORDS and j + 1 < len(rest) and rest[j + 1].low in L.COLORS:
                a, b = t.start, rest[j + 1].end
                attrs.append(Attribute(type="color", value=f"{w} {rest[j + 1].low}", evidence=self._ev(a, b),
                                       span=[a, b]))
                j += 2
                continue
            typ = ("color" if w in L.COLORS else "size" if w in L.SIZES else "material" if w in L.MATERIALS
                   else "other" if w in L.OTHER_ADJ else None)
            if typ:
                attrs.append(Attribute(type=typ, value=w, evidence=t.text, span=[t.start, t.end]))
            elif w.endswith(("'s", "’s")):
                others.append(w)
            else:
                cand.append(t)
            j += 1
        if not cand and attrs and attrs[-1].value == "orange" and (det or count is not None):
            # "an orange": the fruit, not the colour (only colour word that is also a common noun here)
            cand = [t for t in rest if t.low == "orange"][-1:]
            attrs = attrs[:-1]
        if not cand:
            return {"head": None, "mods": bool(attrs or others or count is not None), "toks": ts}
        n_comp = 1
        for n in (3, 2):
            if len(cand) >= n and tuple(c.low for c in cand[-n:]) in (L.COMPOUND_NOUNS | set(L.ENV_PLACES_MULTI)):
                n_comp = n
                break
        head_toks = cand[-n_comp:]
        others += [c.low for c in cand[:-n_comp]]
        surface = " ".join(h.low for h in head_toks)
        lem_last, plural = lemma(head_toks[-1].low)
        name = " ".join([h.low for h in head_toks[:-1]] + [lem_last])
        base_name = name
        if complement:
            name += " of " + " ".join(complement)
        return {"head": head_toks[-1].low, "surface": surface, "name": name, "plural": plural, "attrs": attrs,
                "others": others, "count": count, "kind": kind, "quant": quant, "det": det, "toks": ts,
                "compound": n_comp > 1, "lemma": lem_last, "base_name": base_name}

    def _finish_counts(self, p: dict):
        count, kind, det, plural, lem = p["count"], p["kind"], p["det"], p["plural"], p["lemma"]
        if lem in L.MASS_NOUNS and kind is None and not p["compound"]:
            return None, "unspecified"
        if kind is not None:
            return count, kind
        if det in ("these", "those"):
            return None, "plural_unspecified"
        if det in ("a", "an", "the", "this", "that", "each", "every", "another") and plural is False:
            return 1, "exact"
        if plural:
            return None, "plural_unspecified"
        return None, "unspecified"

    # ---------------- main ----------------
    def run(self) -> PromptAnalysis:
        self.mark_all()
        elems = self._elements()
        E: list[dict] = []      # resolved elements: NP / REL / FRAME / ACTION / BREAK / UNSUP / NEGNP
        groups: dict[str, list[str]] = {}
        neg = False
        carry: list[Tok] = []
        pending_or = False
        last_np: Optional[str] = None
        coord_next = False
        for idx, el in enumerate(elems):
            t = el["t"]
            if t == "SEG":
                toks = carry + el["toks"]
                carry = []
                p = self._parse_np(toks)
                if p is None:
                    continue
                if p["head"] is None:
                    nxt = elems[idx + 1] if idx + 1 < len(elems) else None
                    if p["mods"] and nxt and nxt["t"] == "CONN":
                        carry = toks
                    continue
                a, b = p["toks"][0].start, p["toks"][-1].end
                if p["head"] in L.PRONOUNS:
                    self._add_amb("PRONOUN", f"'{p['head']}' refers to something outside the prompt; ignored.", [a, b])
                    E.append({"t": "NEGNP"})
                    continue
                if neg:
                    if (coord_next or pending_or) and (p["det"] or p["count"] is not None):
                        self._add_amb("NEGATION_SCOPE", f"'{self._ev(a, b)}' follows a negation; treated as "
                                                        "negated (absent), not as an object to draw.", [a, b])
                    self.negations.append(Negation(text=p["name"], evidence=self._ev(a, b), span=[a, b]))
                    E.append({"t": "NEGNP"})
                    continue
                ident = self._emit(p, a, b)
                if p["lemma"] in L.VAGUE_NOUNS:
                    self._add_amb("VAGUE_NOUN", f"'{p['head']}' does not say what to draw.", [a, b])
                if pending_or and last_np:
                    self._add_amb("ALTERNATIVES", f"The prompt offers alternatives ({last_np} or {ident}); "
                                                  "it does not say which one is wanted.", [a, b])
                if coord_next and last_np and last_np in {m for g in groups.values() for m in g}:
                    gid = next(k for k, g in groups.items() if last_np in g)
                    groups[gid].append(ident)
                else:
                    groups[ident] = [ident]
                E.append({"t": "NP", "id": ident, "kind": "env" if ident[0] in "ew" else "object",
                          "setting": False, "span": [a, b]})
                last_np, pending_or, coord_next = ident, False, False
            elif t == "CONN":
                pending_or = pending_or or (el["word"] == "or")
                coord_next = True
                if el["word"] == "and" and idx > 0 and elems[idx - 1]["t"] == "CONN" and elems[idx - 1]["word"] == ",":
                    neg = False  # ", and ..." starts a new item, so the negation ends
            elif t == "NEGP":
                neg = True  # stays on across "and"/"or"/"," until a relation, action or sentence break
                pending_or = coord_next = False
            else:  # REL | FRAME | UNSUP | ACTION | BREAK | SEP
                neg, pending_or, coord_next = False, False, False
                if t != "SEP":
                    E.append(el)
                if t == "BREAK":
                    last_np = None
        self._resolve(E, groups)
        return self._build()

    def _emit(self, p: dict, a: int, b: int) -> str:
        head = p["head"]
        if p["det"] == "the" and p["plural"] is not True and not p["attrs"] and not p["others"] and p["count"] is None:
            for item in [*self.objects, *self.env]:  # "the fox" after "a fox" is the same fox
                if (item.name == p["name"] or getattr(item, "name", None) == p["base_name"]):
                    return item.id
        is_env = (p["lemma"] in L.WEATHER_NOUNS or head in L.ENV_PLACES or p["lemma"] in L.ENV_PLACES
                  or p["surface"] in L.ENV_PLACES_MULTI.values())
        if is_env:
            self._e += 1
            cat = "weather" if p["lemma"] in L.WEATHER_NOUNS else "place"
            ident = f"e{self._e}"
            self.env.append(EnvironmentItem(id=ident, name=p["base_name"], category=cat, attributes=p["attrs"],
                                            evidence=self._ev(a, b), span=[a, b]))
            return ident
        count, kind = self._finish_counts(p)
        self._o += 1
        ident = f"o{self._o}"
        if p["plural"] is None and kind == "unspecified" and p["head"] in L.UNCHANGED_PLURAL and p["det"] is None:
            self._add_amb("NUMBER_AMBIGUOUS", f"'{p['head']}' can be singular or plural; no count given.", [a, b])
        self.objects.append(SceneObject(
            id=ident, name=p["name"], surface=p["surface"], count=count, count_kind=kind, quantifier=p["quant"],
            attributes=p["attrs"], other_modifiers=p["others"],
            lexicon_match=(p["lemma"] in L.KNOWN_NOUNS or p["compound"]), evidence=self._ev(a, b), span=[a, b]))
        return ident

    # ---------------- relations ----------------
    def _resolve(self, E: list[dict], groups: dict[str, list[str]]):
        objs = {o.id: o for o in self.objects}
        # mark environment nouns that are just the setting of a place preposition ("in a forest")
        for i, e in enumerate(E):
            if e["t"] == "REL" and e["kind"] == "place" and i + 1 < len(E) and E[i + 1]["t"] == "NP":
                if E[i + 1]["kind"] == "env":
                    E[i + 1]["setting"] = True
        targets: dict[str, str] = {}
        for i, e in enumerate(E):
            t = e["t"]
            if t == "ACTION":
                tgt = E[i - 1] if i > 0 and E[i - 1]["t"] == "NP" else (E[i + 1] if i + 1 < len(E) and E[i + 1]["t"] == "NP" else None)
                if tgt and tgt["kind"] == "object":
                    objs[tgt["id"]].actions.append(e["word"])
            elif t == "FRAME":
                k = i - 1
                while k >= 0 and E[k]["t"] == "ACTION":
                    k -= 1
                tgt = E[k] if k >= 0 and E[k]["t"] == "NP" else None
                if tgt and tgt["kind"] == "object":
                    objs[tgt["id"]].frame_position = e["value"]
                else:
                    self._add_amb("FRAME_POSITION_NO_SUBJECT",
                                  f"'{e['phrase']}' is not attached to an object.", [e["start"], e["start"] + len(e["phrase"])])
            elif t == "UNSUP":
                self._add_amb("UNSUPPORTED_RELATION", f"'{e['phrase']}' relation is not supported; no relation recorded.")
            elif t == "REL":
                self._relation(E, i, e, groups, targets)

    def _relation(self, E, i, e, groups, targets):
        kind, canon, phrase, span = e["kind"], e["canon"], e["phrase"], e["span"]
        # Subject = nearest earlier noun phrase, preferring one that is not merely a setting ("in a forest").
        prev = None
        fallback = None
        for k in range(i - 1, -1, -1):
            if E[k]["t"] == "BREAK":
                break
            if E[k]["t"] == "NP":
                if E[k]["kind"] == "env" and E[k]["setting"]:
                    fallback = fallback or E[k]
                    continue
                prev = E[k]
                break
        prev = prev or fallback
        nxt = E[i + 1] if i + 1 < len(E) and E[i + 1]["t"] == "NP" else None
        if kind == "unsupported":
            self._add_amb("UNSUPPORTED_RELATION", f"'{phrase}' relation is not supported; objects kept without a relation.", span)
            return
        if kind == "place" and nxt and nxt["kind"] == "env":
            return  # "in a forest": a setting, already captured in `environment`
        if kind == "place" and canon == "at":
            self._add_amb("UNSUPPORTED_RELATION", f"'{phrase}' relation is not supported; objects kept without a relation.", span)
            return
        if prev is None and nxt is None:
            return
        if nxt is None:
            self._add_amb("RELATION_MISSING_OBJECT", f"'{phrase}' has nothing after it to relate to.", span)
            return
        if prev is None:
            self._add_amb("RELATION_MISSING_SUBJECT", f"'{phrase}' has nothing before it to relate; no subject assumed.", span)
        if canon == "above" and e["key"] == ("over",):
            self._add_amb("OVER_AMBIGUOUS", "'over' can mean above or covering; recorded as 'above'.", span)
        if e["key"] == ("by",):
            self._add_amb("BY_AMBIGUOUS", "'by' can mean near or 'made by'; recorded as 'near'.", span)
        subj = prev["id"] if prev else None
        self.relations.append(Relation(subject=subj, relation=canon, object=nxt["id"], spatial=(kind != "with"),
                                       evidence=phrase, span=span))
        if subj:
            if subj in targets and subj.startswith("o"):
                self._add_amb("RELATION_ATTACHMENT",
                              f"'{phrase}' was attached to the nearest noun phrase ({subj}); it may instead "
                              f"describe {targets[subj]}.", span)
            g = next((m for m in groups.values() if subj in m), None)
            if g and len(g) > 1 and g[-1] == subj:
                self._add_amb("RELATION_SCOPE", f"'{phrase}' may apply to all of {', '.join(g)}, not only {subj}.", span)
        targets[nxt["id"]] = subj or "?"

    # ---------------- output ----------------
    def _build(self) -> PromptAnalysis:
        env = sorted(self.env, key=lambda x: x.span[0])
        n_attr = sum(len(o.attributes) for o in self.objects)
        n_obj, n_rel = len(self.objects), len(self.relations)
        level = "complex" if (n_obj >= 3 or n_rel >= 2) else "moderate" if (n_obj == 2 or n_rel == 1) else "simple"
        if not self.objects and not env:
            self._add_amb("NO_OBJECTS_FOUND", "No object or scene noun could be identified.")
        ascii_letters = sum(c.isascii() and c.isalpha() for c in self.raw)
        other_letters = sum((not c.isascii()) and c.isalpha() for c in self.raw)
        if other_letters > ascii_letters:
            self._add_amb("UNSUPPORTED_LANGUAGE", "Parser rules are English-only; extraction is unreliable.")
        return PromptAnalysis(
            raw_prompt=self.raw, validation=Validation(), objects=self.objects, environment=env,
            relations=self.relations, lighting=sorted(self.lighting, key=lambda x: x.span[0]),
            style=sorted(self.style, key=lambda x: x.span[0]), negations=self.negations, ambiguities=self.amb,
            complexity=Complexity(object_count=n_obj, relation_count=n_rel, attribute_count=n_attr, level=level))


def analyze_prompt(prompt: str) -> PromptAnalysis:
    """Analyse prompt TEXT. Never raises for str input; invalid prompts return validation.valid=False."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str")
    empty = Complexity(object_count=0, relation_count=0, attribute_count=0, level="simple")
    if not prompt.strip():
        return PromptAnalysis(raw_prompt=prompt, complexity=empty,
                              validation=Validation(valid=False, code="EMPTY_PROMPT", message="Prompt is empty."))
    if len(prompt) > MAX_PROMPT_CHARS:
        return PromptAnalysis(raw_prompt=prompt, complexity=empty,
                              validation=Validation(valid=False, code="TOO_LONG",
                                                    message=f"Prompt exceeds {MAX_PROMPT_CHARS} characters."))
    return _Parser(prompt).run()
