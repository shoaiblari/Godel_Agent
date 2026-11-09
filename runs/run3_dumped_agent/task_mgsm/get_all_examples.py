

def get_all_examples(): #-> list[dict[str, str]]:
    examples = []
    for lang in ALL_LANGUAGES:
        # if lang != "en":
        #     continue
        examples += get_lang_examples(lang)
    return examples
