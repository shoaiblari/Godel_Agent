

def get_lang_examples(lang: str): #-> list[dict[str, str]]:
    fpath = LANG_TO_FPATH(lang)
    examples = []
    with open(fpath, mode='r', encoding='utf-8') as f:
        for line in f:
            inputs, targets = line.strip().split("\t")
            if "." in targets:
                raise ValueError(f"targets {targets} contains a decimal point.")
            # targets = int(targets.replace(",", ""))
            examples.append({"inputs": LANG_TO_INSTRUCTIONS[lang].format(input=inputs), "targets": targets, "lang": lang})
    return examples
