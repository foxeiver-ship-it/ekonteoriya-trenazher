#!/usr/bin/env python3
"""Собирает trainer/build/банк.js из базы вопросов, разметки тем и разборов.

Источники лежат в соседнем проекте ~/Documents/Экзамен-база:
  база.json, разбор/темы.json, разбор/темы-вопросов.json,
  разбор/разборы/выход-*.json

Запуск: python3 trainer/собрать-банк.py
"""

import json
import re
from glob import glob
from pathlib import Path

КОРЕНЬ = Path(__file__).resolve().parent.parent
ИСТОЧНИК = Path.home() / "Documents" / "Экзамен-база"
ВЫХОД = КОРЕНЬ / "trainer" / "build" / "банк.js"

ТИПЫ = {"multichoice": "one", "shortanswer": "short", "match": "match"}


def разобрать_пары(текст):
    пары = []
    for строка in текст.splitlines():
        if "→" in строка:
            слева, справа = строка.split("→", 1)
            пары.append({"l": слева.strip(), "r": справа.strip()})
    return пары


def main():
    база = json.loads((ИСТОЧНИК / "база.json").read_text(encoding="utf-8"))
    темы = json.loads((ИСТОЧНИК / "разбор" / "темы.json").read_text(encoding="utf-8"))
    тема_вопроса = json.loads(
        (ИСТОЧНИК / "разбор" / "темы-вопросов.json").read_text(encoding="utf-8")
    )

    разборы = {}
    for файл in glob(str(ИСТОЧНИК / "разбор" / "разборы" / "выход-*.json")):
        for запись in json.loads(Path(файл).read_text(encoding="utf-8")):
            разборы[запись["id"]] = запись

    банк, пропуски = [], []
    for в in база:
        р = разборы.get(в["id"])
        if not р:
            пропуски.append(в["id"])
            continue
        тип = ТИПЫ[в["тип"]]
        вопрос = {
            "id": в["id"],
            "t": int(тема_вопроса.get(в["id"], 0)),
            "ty": тип,
            "q": re.sub(r"\s+\n", "\n", в["текст"]).strip(),
            "o": [],
            "a": [],
            "pairs": [],
            "pool": [],
            "ans": "",
            "img": None,
            "e": р["e"],
            "w": [],
            "k": р["k"],
        }
        if в["тип"] == "multichoice":
            вопрос["o"] = [х["текст"] for х in в["варианты"]]
            вопрос["a"] = [i for i, х in enumerate(в["варианты"]) if х["верный"]]
            вопрос["w"] = р["w"]
            if len(вопрос["a"]) > 1 or в.get("несколько_ответов"):
                вопрос["ty"] = "many"
        elif в["тип"] == "shortanswer":
            вопрос["ans"] = в["ответ"].strip()
        else:
            вопрос["pairs"] = разобрать_пары(в["ответ"])
            вопрос["pool"] = sorted({о for п in в["пары"] for о in п["варианты"]})
        банк.append(вопрос)

    строки = [
        "// Файл собран скриптом trainer/собрать-банк.py — правки вносите в источники.",
        "window.ТЕМЫ = "
        + json.dumps(
            [{"n": т["n"], "название": т["название"]} for т in темы],
            ensure_ascii=False,
        )
        + ";",
        "window.БАНК = [",
    ]
    строки += [json.dumps(в, ensure_ascii=False) + "," for в in банк]
    строки.append("];")
    ВЫХОД.write_text("\n".join(строки) + "\n", encoding="utf-8")

    print(f"Вопросов: {len(банк)}, тем: {len(темы)}, без разбора: {len(пропуски)}")
    if пропуски:
        print("Без разбора:", " ".join(пропуски[:20]))


if __name__ == "__main__":
    main()
