import language_tool_python


LANGUAGES = {
    "English": "en-US",
    "Spanish": "es",
    "French": "fr",
    "Italian": "it",
    "Japanese": "ja",
    "Chinese": "zh-CN",
}


TESTS = {
    "English": [
        # Learner writing
        "Yesterday I go to the store with my friend and we buy some food.",
        "I have been study English for two years and I really like it.",
        "My friend don't like coffee but she drink tea every morning.",
        "Last weekend was very fun because I meet many new people.",
        "I want to improve my English because sometimes I have difficult to express my ideas.",

        # Correct
        "Yesterday I went to the store with my friend and we bought some food.",
    ],

    "Spanish": [
        # Learner writing
        "Ayer fui al parque con mi amiga y nosotros comer pizza después porque estaba muy cansado.",
        "Yo estudio español desde dos años y quiero hablar con más confianza.",
        "Mi amiga no gusta el café pero ella bebe té cada mañana.",
        "El fin de semana pasado fue muy divertido porque conozco muchas personas nuevas.",
        "Quiero mejorar mi español porque a veces tengo difícil expresar mis ideas.",

        # Correct
        "Ayer fui al parque con mi amiga y comimos pizza después.",
    ],

    "French": [
        # Learner writing
        "Hier je suis allé au parc avec mon amie et nous manger une pizza après.",
        "J'étudie le français depuis deux ans et je veux parler avec plus de confiance.",
        "Mon amie n'aime pas le café mais elle boire du thé chaque matin.",
        "Le week-end dernier était très amusant parce que je rencontre beaucoup de nouvelles personnes.",
        "Je veux améliorer mon français parce que parfois j'ai difficile à exprimer mes idées.",

        # Correct
        "Hier je suis allé au parc avec mon amie et nous avons mangé une pizza.",
    ],

    "Italian": [
        # Learner writing
        "Ieri sono andato al parco con la mia amica e noi mangiare una pizza dopo.",
        "Studio italiano da due anni e voglio parlare con più fiducia.",
        "La mia amica non piace il caffè ma lei beve il tè ogni mattina.",
        "Lo scorso fine settimana era molto divertente perché incontro molte persone nuove.",
        "Voglio migliorare il mio italiano perché a volte ho difficile esprimere le mie idee.",

        # Correct
        "Ieri sono andato al parco con la mia amica e abbiamo mangiato una pizza.",
    ],

    "Japanese": [
        # Learner writing
        "昨日は友達と一緒に映画を見に行きました。映画はとても面白かったですが、少し長いでした。",
        "私は日本語を二年間勉強して、もっと自信を持って話したいです。",
        "私の友達はコーヒーが好きじゃないですが、毎朝お茶を飲みます。",
        "先週末はとても楽しかったです。たくさん新しい人に会いました。",
        "日本語を上手になりたいです。時々自分の考えを表現することが難しいです。",

        # Correct
        "昨日は友達と一緒に映画を見に行きました。映画はとても面白かったです。",
    ],

    "Chinese": [
        # Learner writing
        "昨天我和朋友一起去公园然后我们吃披萨，因为我很累。",
        "我学习中文两年了，我想要更有自信地说中文。",
        "我的朋友不喜欢咖啡，但是她每天早上喝茶。",
        "上个周末非常有意思，因为我认识了很多新的人。",
        "我想提高我的中文，因为有时候表达我的想法很困难。",

        # Correct
        "昨天我和朋友一起去公园，然后我们吃了披萨。",
    ],
}


def print_match(match):
    print("  " + "-" * 58)
    print(f"  RULE ID:       {match.rule_id}")
    print(f"  ISSUE TYPE:    {match.rule_issue_type}")
    print(f"  CATEGORY:      {match.category}")
    print(f"  MESSAGE:       {match.message}")
    print(f"  OFFSET:        {match.offset}")
    print(f"  ERROR LENGTH:  {match.error_length}")
    print(f"  REPLACEMENTS:  {match.replacements}")
    print(f"  CONTEXT:       {match.context}")
    print(f"  SENTENCE:      {match.sentence}")


def test_language(language_name, language_code):
    print("\n")
    print("#" * 70)
    print(f"LANGUAGE: {language_name} ({language_code})")
    print("#" * 70)

    tool = language_tool_python.LanguageTool(language_code)

    for index, text in enumerate(TESTS[language_name], start=1):
        print("\n" + "=" * 60)
        print(f"TEST {index}")
        print("TEXT:", text)

        matches = tool.check(text)

        if not matches:
            print("  ✓ No corrections found")
        else:
            print(f"  FOUND {len(matches)} MATCH(ES)")

            for match in matches:
                print_match(match)

    tool.close()


def main():
    print("Starting LanguageTool realistic learner-writing benchmark...")
    print()

    for language_name, language_code in LANGUAGES.items():
        test_language(language_name, language_code)

    print("\n")
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()