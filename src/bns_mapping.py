"""IPC (1860) to BNS (Bharatiya Nyaya Sanhita, 2023) section mapping.

Covers the most commonly referenced IPC provisions and their BNS equivalents
per the official correspondence table (Ministry of Home Affairs, 2024).
"""

from __future__ import annotations

import re

# IPC section → (BNS section, short description)
IPC_TO_BNS: dict[str, tuple[str, str]] = {
    "34": ("3(5)", "Common intention"),
    "96": ("34", "Right of private defence"),
    "97": ("35", "Right of private defence of body and property"),
    "100": ("38", "When right extends to causing death"),
    "107": ("45", "Abetment of a thing"),
    "109": ("47", "Punishment of abetment"),
    "120A": ("61(1)", "Criminal conspiracy — definition"),
    "120B": ("61(2)", "Criminal conspiracy — punishment"),
    "121": ("147", "Waging war against India"),
    "124A": ("152", "Acts endangering sovereignty"),
    "141": ("189", "Unlawful assembly"),
    "147": ("194", "Rioting"),
    "148": ("195", "Rioting armed with deadly weapon"),
    "149": ("196", "Vicarious liability — unlawful assembly"),
    "153A": ("196", "Promoting enmity between groups"),
    "191": ("227", "Giving false evidence"),
    "193": ("229", "Punishment for false evidence"),
    "299": ("100", "Culpable homicide"),
    "300": ("101", "Murder"),
    "302": ("103", "Punishment for murder"),
    "303": ("103(2)", "Murder by life-convict"),
    "304": ("105", "Culpable homicide not amounting to murder"),
    "304A": ("106", "Causing death by negligence"),
    "304B": ("80", "Dowry death"),
    "306": ("108", "Abetment of suicide"),
    "307": ("109", "Attempt to murder"),
    "308": ("110", "Attempt to commit culpable homicide"),
    "309": ("Decriminalised", "Attempt to commit suicide"),
    "319": ("114", "Hurt"),
    "320": ("117", "Grievous hurt"),
    "323": ("115", "Voluntarily causing hurt"),
    "324": ("118", "Hurt by dangerous weapons"),
    "325": ("117", "Voluntarily causing grievous hurt"),
    "326": ("118", "Grievous hurt by dangerous weapons"),
    "326A": ("124", "Acid attack"),
    "339": ("126", "Wrongful restraint"),
    "340": ("127", "Wrongful confinement"),
    "354": ("74", "Assault on woman — outraging modesty"),
    "354A": ("75", "Sexual harassment"),
    "354B": ("76", "Assault with intent to disrobe"),
    "354C": ("77", "Voyeurism"),
    "354D": ("78", "Stalking"),
    "359": ("134", "Kidnapping"),
    "363": ("137", "Punishment for kidnapping"),
    "364A": ("140", "Kidnapping for ransom"),
    "375": ("63", "Rape — definition"),
    "376": ("63(2)", "Punishment for rape"),
    "376A": ("66", "Intercourse by person in authority"),
    "378": ("303", "Theft"),
    "379": ("303(2)", "Punishment for theft"),
    "380": ("305", "Theft in dwelling house"),
    "383": ("308", "Extortion"),
    "390": ("309", "Robbery"),
    "391": ("310", "Dacoity"),
    "392": ("309(2)", "Punishment for robbery"),
    "395": ("310(2)", "Punishment for dacoity"),
    "396": ("310(3)", "Dacoity with murder"),
    "405": ("316", "Criminal breach of trust"),
    "406": ("316(2)", "Punishment — criminal breach of trust"),
    "409": ("316(5)", "By public servant / banker"),
    "415": ("318", "Cheating"),
    "420": ("318(4)", "Cheating — inducing delivery of property"),
    "425": ("324", "Mischief"),
    "441": ("329(1)", "Criminal trespass"),
    "447": ("329(4)", "Punishment for criminal trespass"),
    "448": ("329(5)", "House-trespass"),
    "463": ("336", "Forgery"),
    "465": ("338", "Punishment for forgery"),
    "467": ("340", "Forgery of valuable security"),
    "468": ("341", "Forgery for purpose of cheating"),
    "471": ("344", "Using forged document as genuine"),
    "494": ("82", "Bigamy"),
    "498A": ("85", "Cruelty by husband or relatives"),
    "499": ("356", "Defamation"),
    "500": ("356(2)", "Punishment for defamation"),
    "503": ("351", "Criminal intimidation"),
    "504": ("352", "Intentional insult — breach of peace"),
    "506": ("351(2)", "Punishment for criminal intimidation"),
    "509": ("79", "Word / gesture insulting modesty of woman"),
    "511": ("62", "Attempting to commit offences"),
}

_SECTION_RE = re.compile(
    r"(?:section|sec\.?|s\.?|ipc)\s*(\d+[A-Z]*)",
    re.IGNORECASE,
)


def get_bns_equivalent(ipc_section: str) -> tuple[str, str] | None:
    cleaned = ipc_section.strip().upper()
    for prefix in ("SECTION ", "SEC. ", "SEC ", "S. ", "S ", "IPC "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    return IPC_TO_BNS.get(cleaned)


def extract_bns_notes(text: str) -> list[str]:
    """Scan text for IPC section references and return BNS equivalents found."""
    seen: set[str] = set()
    notes: list[str] = []
    for m in _SECTION_RE.finditer(text):
        sec = m.group(1).upper()
        if sec in seen:
            continue
        seen.add(sec)
        result = IPC_TO_BNS.get(sec)
        if result:
            bns_sec, desc = result
            notes.append(f"IPC Section {sec} ({desc}) → BNS Section {bns_sec}")
    return notes


def bns_context_for_prompt(query: str, context: str) -> str:
    """Build a BNS note block to append to the LLM context."""
    notes = extract_bns_notes(query + "\n" + context)
    if not notes:
        return ""
    return (
        "\n\nIMPORTANT — BNS equivalents (IPC replaced by Bharatiya Nyaya Sanhita, 2023, "
        "effective 1 July 2024):\n" + "\n".join(f"  • {n}" for n in notes)
    )
