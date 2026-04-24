import vertexai
from vertexai.generative_models import GenerativeModel

_model: GenerativeModel | None = None
_MODEL = "gemini-2.5-flash"

_PROMPT = """Sen professional o'zbek jurnalistisan. Quyidagi xorijiy yangilikni o'zbek tiliga (lotin yozuvi) tabiiy, jurnalistik uslubda tarjima qil.

Qoidalar:
- Sarlavhani qisqa va jozibali qil
- Tavsifni 2-3 gapga sig'dir
- Familiyalar va joy nomlarini o'zbekcha transliteratsiyada yoz (masalan: Messi, Ronaldo, Barselona, Madrid)
- Klub va liga nomlarini o'zbekchada qabul qilingan shaklda yoz (masalan: "Manchester Yunayted", "Real Madrid", "Premier-liga", "Chempionlar ligasi")
- Original ma'noni saqla, o'zingdan qo'shma
- Javobni AYNAN shu formatda ber, boshqa hech narsa qo'shmasdan:

TITLE: <tarjima qilingan sarlavha>
SUMMARY: <tarjima qilingan tavsif>

---
Original til: {lang}
Original sarlavha: {title}
Original tavsif: {summary}
"""


def init(project: str, location: str = "us-central1") -> None:
    global _model
    vertexai.init(project=project, location=location)
    _model = GenerativeModel(_MODEL)


def translate_to_uzbek(title: str, summary: str, src_lang: str) -> tuple[str, str]:
    if src_lang == "uz":
        return title, summary

    assert _model is not None, "translator.init() chaqirilmagan"

    prompt = _PROMPT.format(lang=src_lang, title=title, summary=summary or "(tavsif yo'q)")

    resp = _model.generate_content(prompt)
    text = (resp.text or "").strip()

    out_title = title
    out_summary = summary
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            out_title = line.split(":", 1)[1].strip()
        elif line.upper().startswith("SUMMARY:"):
            out_summary = line.split(":", 1)[1].strip()

    return out_title, out_summary
