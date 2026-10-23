from app.ml.infer import analyze_text


def test_explicit_abuse_is_not_uncertain():
    result = analyze_text("tum bohat stupid ho", include_xai=False)
    assert result["classification"] == "BULLYING"
    assert result["risk"] != "REVIEW"
    assert result["confidence"] >= 0.68


def test_benign_engagement_stays_safe():
    result = analyze_text("If u like this song then like this comment", include_xai=False)
    assert result["classification"] == "SAFE"
    assert result["risk"] == "LOW"


def test_benign_praise_and_grief_stay_safe():
    praise = analyze_text(
        "No hate, Bro you guys are exceptionally good, but there is no parallel of that bonefire video.",
        include_xai=False,
    )
    grief = analyze_text(
        "I am out from my home and I miss my grandmother so much she is alive now",
        include_xai=False,
    )
    assert praise["classification"] == "SAFE"
    assert grief["classification"] == "SAFE"


def test_roman_urdu_insults_are_bullying():
    result = analyze_text("Tum bohat pagal aur kharab ho", include_xai=False)
    assert result["classification"] == "BULLYING"
    assert result["risk"] != "REVIEW"


def test_religious_praise_and_favorites_stay_safe():
    texts = [
        "a Allah G Ya Muhammad SAw I Love you",
        "My favourite Kalam",
        "my favourite qasida",
    ]
    for text in texts:
        result = analyze_text(text, include_xai=False)
        assert result["classification"] == "SAFE"
        assert result["risk"] == "LOW"


def test_patriotic_and_positive_messages_stay_safe():
    texts = [
        "I LOVE INDIA",
        "RANG MEIN BASA HINDUSTAN",
        "love you sir god bless you",
    ]
    for text in texts:
        result = analyze_text(text, include_xai=False)
        assert result["classification"] == "SAFE"
        assert result["risk"] == "LOW"
