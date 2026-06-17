from __future__ import annotations

IRODORI_EMOJI_TABLE: tuple[tuple[str, str], ...] = (
    ("👂", "囁き、耳元の音"),
    ("😮‍💨", "吐息、溜息、寝息"),
    ("⏸️", "間、沈黙"),
    ("🤭", "笑い、くすくす、含み笑い"),
    ("🥵", "喘ぎ、うめき声、唸り声"),
    ("📢", "エコー、リバーブ"),
    ("😏", "からかうように、甘えるように"),
    ("🥺", "声を震わせながら、自信なさげに"),
    ("🌬️", "息切れ、荒い息遣い、呼吸音"),
    ("😮", "息をのむ"),
    ("👅", "舐める音、咀嚼音、水音"),
    ("💋", "リップノイズ"),
    ("🫶", "優しく"),
    ("😭", "嗚咽、泣き声、悲しみ"),
    ("😱", "悲鳴、叫び、絶叫"),
    ("😪", "眠そうに、気だるげに"),
    ("💤", "寝言、いびき"),
    ("⏩", "早口、一気にまくしたてる、急いで"),
    ("📞", "電話越し、スピーカー越しのような音"),
    ("🐢", "ゆっくりと"),
    ("🥤", "唾を飲み込む音"),
    ("🤧", "咳き込み、鼻すすり、くしゃみ、咳払い"),
    ("😒", "舌打ち"),
    ("😰", "慌てて、動揺、緊張、どもり"),
    ("😆", "喜びながら"),
    ("💨", "勢いよく、勢いに任せて"),
    ("😠", "怒り、不満げ、拗ねながら"),
    ("😲", "驚き、感嘆"),
    ("🥱", "あくび"),
    ("😖", "苦しげに"),
    ("😟", "心配そうに"),
    ("🫣", "恥ずかしそうに、照れながら"),
    ("🙄", "呆れたように"),
    ("😊", "楽しげに、嬉しそうに"),
    ("😤", "得意げに、自信ありげに"),
    ("👌", "相槌、頷く音"),
    ("🙏", "懇願するように"),
    ("🥴", "酔っ払って"),
    ("🎵", "鼻歌"),
    ("🤐", "口を塞がれて"),
    ("😌", "安堵、満足げに"),
    ("🤔", "疑問の声"),
    ("💪", "力を込めて、力強く"),
    ("👃", "匂いを嗅ぐ音"),
    ("📖", "ナレーション、独白、モノローグ"),
)

ALLOWED_IRODORI_EMOJIS = frozenset(emoji for emoji, _ in IRODORI_EMOJI_TABLE)
DEFAULT_EMOJI = "📖"


def emoji_markdown_table() -> str:
    rows = ["| 絵文字 | 音声表現 |", "|---|---|"]
    rows.extend(f"| {emoji} | {description} |" for emoji, description in IRODORI_EMOJI_TABLE)
    return "\n".join(rows)


def extract_initial_emoji(text: str) -> tuple[str | None, str]:
    stripped = text.strip()
    for emoji in sorted(ALLOWED_IRODORI_EMOJIS, key=len, reverse=True):
        if stripped.startswith(emoji):
            return emoji, stripped[len(emoji):].strip()
    return None, stripped


def ensure_initial_emoji(text: str, default_emoji: str = DEFAULT_EMOJI) -> str:
    emoji, body = extract_initial_emoji(text)
    if emoji:
        return f"{emoji}{body}"
    return f"{default_emoji}{body}"


def remove_initial_emoji(text: str) -> str:
    _, body = extract_initial_emoji(text)
    return body
