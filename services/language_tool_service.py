import language_tool_python

# These language were specifically tested with language tool
SUPPORTED_LANGUAGES = {
    "English": "en-US",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
}


_tools = {}


def get_language_tool(language):
    language_code = SUPPORTED_LANGUAGES.get(language)

    if not language_code:
        return None

    if language_code not in _tools:
        print(f"Starting LanguageTool for {language_code}...")
        _tools[language_code] = language_tool_python.LanguageTool(
            language_code
        )

    return _tools[language_code]


def check_text(text, language):
    tool = get_language_tool(language)

    if tool is None:
        return []

    return tool.check(text)