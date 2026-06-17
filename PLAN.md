# radio-sucrose Implementation Plan

This document is the handoff plan for implementing `radio-sucrose`. It is intentionally detailed so work can resume after a context/window reset or rate-limit interruption.

## Critical continuity and commit discipline

- Treat this file as the authoritative implementation checklist and recovery guide.
- Keep commit granularity high: commit each small, working slice before moving to the next slice.
- Do not accumulate large uncommitted source changes.
- If the session approaches 98% of the model/rate-limit/context budget, immediately stop feature work, discard any unsafe or incomplete source changes that are not needed, and ensure the repository can reproduce the most recent committed state.
- Before any large edit, check `git status --short`; after the edit, run the smallest relevant check and commit if the slice is coherent.
- Prefer small, revertible commits over large implementation bursts.
- `./refs/` is intentionally untracked because it may contain private character corpora, reference voices, API keys, OBS credentials, or other local-only secrets.

## Product goal

Build a YouTube live radio application where two characters discuss fresh news, answer Super Chats as listener letters, and fill gaps with structured idle talk. The runtime stack is:

- vLLM for script generation.
- Irodori-TTS zero-shot synthesis for character voices.
- Yahoo!ニュース RSS and article pages for news acquisition.
- pytchat for YouTube live chat and Super Chat acquisition.
- obs-websocket for updating an OBS text source named `message_box`.
- SQLite for deduplication, history, queues, and topic memory.

## Speaker and reference data

Local private data is expected under `./refs/`:

```text
refs/
  sucrose.txt
  dori.txt
  sucrose.wav
  dori.wav
```

Speaker mapping:

- Speaker A: スクロース
  - Role: radio personality / host.
  - Dialogue corpus: `./refs/sucrose.txt`.
  - Irodori-TTS reference audio: `./refs/sucrose.wav`.
  - Responsibilities: opening, news introduction, summary, transitions, listener-letter/Super Chat introduction, closing.
- Speaker B: ドリー
  - Role: guest.
  - Dialogue corpus: `./refs/dori.txt`.
  - Irodori-TTS reference audio: `./refs/dori.wav`.
  - Responsibilities: reactions, questions, listener perspective, idle-talk expansion, guest commentary.

## vLLM serving plan

The fixed dialogue corpus is estimated at 55,297 tokens. Keep it at the start of the prompt so vLLM prefix caching can reuse it.

Current serving profile:

```bash
docker run -it --rm \
  --gpus all \
  --ipc=host \
  --network host \
  -v ~/.cache/huggingface:/home/eiichi/.cache/huggingface \
  -e VLLM_ATTENTION_BACKEND=FLASHINFER \
  vllm \
  vllm serve nvidia/Qwen3.6-35B-A3B-NVFP4 \
  --tensor-parallel-size 1 \
  --enable-prefix-caching \
  --pipeline-parallel-size 1 \
  --max-model-len 81920 \
  --gpu-memory-utilization 0.75 \
  --trust-remote-code \
  --max-num-seqs 1 \
  --max-num-batched-tokens 16384 \
  --speculative-config '{"method":"mtp","num_speculative_tokens":3}'
```

Fallback profiles:

- Stability first: `--max-model-len 65536 --gpu-memory-utilization 0.70 --max-num-seqs 1 --max-num-batched-tokens 8192`.
- Current balanced long-context profile: `--max-model-len 81920 --gpu-memory-utilization 0.75 --max-num-seqs 1 --max-num-batched-tokens 16384`.
- Aggressive only after measurement: `--max-model-len 81920 --gpu-memory-utilization 0.82 --max-num-seqs 1 --max-num-batched-tokens 32768`.

Prompt budget rule for `max-model-len=81920`:

- Fixed prefix: 55,297 tokens.
- Dynamic news/comment payload: target <= 8,000 tokens.
- Generated output: target <= 4,000 tokens.
- Keep a large safety headroom for schema, system rules, tokenizer variance, and future prompt growth.

## Prompt construction plan

Prompt order must remain stable:

1. Prompt version.
2. Application role.
3. Speaker definitions.
4. `sucrose.txt` contents.
5. `dori.txt` contents.
6. Irodori-TTS emoji annotation table.
7. Radio progression rules.
8. News rules.
9. Super Chat/listener-letter rules.
10. Idle-talk taxonomy rules.
11. OBS `message_box` rules.
12. JSON output schema.
13. Dynamic request payload.

Do not place date, current news, chat messages, or other variable content before the fixed prefix.

## Irodori-TTS emoji table

Put the full table in the fixed prompt. The table is small compared with the speaker corpus and improves emoji selection quality.

```text
| 絵文字 | 音声表現 |
|---|---|
| 👂 | 囁き、耳元の音 |
| 😮‍💨 | 吐息、溜息、寝息 |
| ⏸️ | 間、沈黙 |
| 🤭 | 笑い、くすくす、含み笑い |
| 🥵 | 喘ぎ、うめき声、唸り声 |
| 📢 | エコー、リバーブ |
| 😏 | からかうように、甘えるように |
| 🥺 | 声を震わせながら、自信なさげに |
| 🌬️ | 息切れ、荒い息遣い、呼吸音 |
| 😮 | 息をのむ |
| 👅 | 舐める音、咀嚼音、水音 |
| 💋 | リップノイズ |
| 🫶 | 優しく |
| 😭 | 嗚咽、泣き声、悲しみ |
| 😱 | 悲鳴、叫び、絶叫 |
| 😪 | 眠そうに、気だるげに |
| 💤 | 寝言、いびき |
| ⏩ | 早口、一気にまくしたてる、急いで |
| 📞 | 電話越し、スピーカー越しのような音 |
| 🐢 | ゆっくりと |
| 🥤 | 唾を飲み込む音 |
| 🤧 | 咳き込み、鼻すすり、くしゃみ、咳払い |
| 😒 | 舌打ち |
| 😰 | 慌てて、動揺、緊張、どもり |
| 😆 | 喜びながら |
| 💨 | 勢いよく、勢いに任せて |
| 😠 | 怒り、不満げ、拗ねながら |
| 😲 | 驚き、感嘆 |
| 🥱 | あくび |
| 😖 | 苦しげに |
| 😟 | 心配そうに |
| 🫣 | 恥ずかしそうに、照れながら |
| 🙄 | 呆れたように |
| 😊 | 楽しげに、嬉しそうに |
| 😤 | 得意げに、自信ありげに |
| 👌 | 相槌、頷く音 |
| 🙏 | 懇願するように |
| 🥴 | 酔っ払って |
| 🎵 | 鼻歌 |
| 🤐 | 口を塞がれて |
| 😌 | 安堵、満足げに |
| 🤔 | 疑問の声 |
| 💪 | 力を込めて、力強く |
| 👃 | 匂いを嗅ぐ音 |
| 📖 | ナレーション、独白、モノローグ |
```

Each `tts_text` chunk must start with exactly one emoji from this table. `display_text` must be suitable for OBS and should normally omit the Irodori-TTS control emoji.

## Output schema

Use a flat chunk list for easy sequential playback:

```json
{
  "segment_type": "news | superchat | idle_talk | comment",
  "target_duration_sec": 180,
  "max_duration_sec": 210,
  "summary_for_memory": "short segment summary",
  "topic": {
    "large_category": "optional for idle_talk",
    "middle_category": "optional for idle_talk",
    "small_category": "optional for idle_talk"
  },
  "chunks": [
    {
      "speaker": "A",
      "speaker_name": "スクロース",
      "tts_text": "📖続いては、今日のニュースです。",
      "display_text": "続いては、今日のニュースです。"
    }
  ]
}
```

Validation rules:

- `speaker` must be `A` or `B`.
- `speaker_name` must match the speaker mapping.
- `tts_text` must start with an allowed Irodori-TTS emoji.
- `display_text` is required and is the only text sent to OBS `message_box`.
- Each chunk should be 50-80 Japanese characters when possible and must be split before it becomes too long for Irodori-TTS.
- If a chunk changes emotion, split it and select an appropriate emoji for the next chunk.

## News segment plan

Target one news segment at around 3 minutes, maximum 3 minutes 30 seconds:

- Target text: 900-1200 Japanese characters.
- Hard cap: 1400 Japanese characters.
- Required structure:
  1. スクロース introduces the news.
  2. スクロース summarizes the key facts.
  3. ドリー reacts or asks a listener-style question.
  4. スクロース adds background or context.
  5. ドリー adds related idle-talk-style conversation tied to the news.
  6. スクロース organizes the point.
  7. ドリー gives a short listener-perspective comment.
  8. スクロース closes naturally and can transition to a listener letter.

Do not interrupt a news segment for Super Chat. Queue Super Chats and read them after the current segment completes.

## Super Chat and listener-letter plan

Super Chats are treated as listener letters, not mid-news interruptions.

- スクロース introduces the letter: `ここで、ラジオネーム○○さんからお便りが届いております。`
- スクロース thanks the sender if it is a Super Chat.
- ドリー reacts as the guest.
- Response depth is based on both amount and content seriousness.
- Short serious consultations must receive a serious response.
- High-value simple thanks should receive warm thanks but not forced long commentary.
- Unsafe or inappropriate content should be skipped or paraphrased safely.

## Idle-talk plan

If there are no news items, Super Chats, or comments, generate an idle-talk segment.

Idle-talk taxonomy has three levels:

- 大分類: broad abstraction.
- 中分類: more concrete abstraction.
- 小分類: concrete object/topic.

Examples to place in the prompt:

```text
旅行・フランス・ノートルダム大聖堂
旅行・オランダ・アムステルダムの運河
旅行・日本・京都の路地
食べ物・食材・馬鈴薯
食べ物・料理・カレー
食べ物・飲み物・紅茶
文化・音楽・ジャズ喫茶
文化・建築・駅舎
生き物・鳥・カラス
生き物・海の生物・クラゲ
科学・宇宙・月面基地
科学・気象・積乱雲
生活・道具・万年筆
生活・習慣・朝の散歩
ゲーム・ジャンル・ローグライク
歴史・時代・江戸時代
言葉・日本語・方言
```

The model should generate new combinations by itself, avoid recent repeats, and structure the conversation around the selected three-level topic.

## Yahoo!ニュース RSS acquisition plan

Use RSS as the primary acquisition path. Start with:

```text
https://news.yahoo.co.jp/rss/topics/top-picks.xml
```

Maintain category feeds for:

- 主要
- 国内
- 国際
- 経済
- エンタメ
- スポーツ
- IT
- 科学
- 地域

RSS parse rule:

```text
rss > channel > item[] > link
```

For each item:

1. Fetch the RSS item link with `requests.get`.
2. Parse with BeautifulSoup4.
3. Search all `a` tags for visible text containing `記事全文を読む`.
4. If found, use the `href` as the full article URL.
5. Fetch the full article URL.
6. Extract title from `header > h1`, falling back to any `h1` and then RSS title.
7. Extract article body from `#uamods > div:nth-of-type(1) > div` by collecting all descendant `p` tags.
8. Fall back to `#uamods`, `article`, then `main` if needed.
9. Join paragraphs with newlines.
10. Store RSS URL, full article URL, title, body, category, source, and timestamps in SQLite.

Do not use markdownify for article extraction. Use BeautifulSoup4 and plain text paragraphs.

Avoid reading article text verbatim in the broadcast. Article bodies are source material for summarization, explanation, and related conversation.

## SQLite plan

Tables to create early:

```sql
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL UNIQUE,
  canonical_url TEXT,
  full_article_url TEXT,
  title TEXT NOT NULL,
  body TEXT,
  source TEXT,
  category TEXT NOT NULL,
  published_at TEXT,
  discovered_at TEXT NOT NULL,
  read_at TEXT,
  status TEXT NOT NULL DEFAULT 'candidate'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_full_article_url
ON articles(full_article_url)
WHERE full_article_url IS NOT NULL;

CREATE TABLE IF NOT EXISTS idle_topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  large_category TEXT NOT NULL,
  middle_category TEXT NOT NULL,
  small_category TEXT NOT NULL,
  used_at TEXT NOT NULL
);
```

Later add queue/history tables as needed.

## OBS integration plan

Use obs-websocket, not Browser Source.

- OBS must contain a text source named `message_box`.
- The app sends only `display_text` to `message_box`.
- TTS control emoji should normally not appear in OBS.

Playback order per chunk:

1. Generate Irodori-TTS audio for `tts_text`.
2. Update OBS `message_box` with `display_text`.
3. Play the generated audio.
4. Add a natural pause.
5. Move to the next chunk.

Use one-chunk prefetch for natural playback:

- Generate chunk N+1 while chunk N is playing.
- Do not concatenate into one long audio file for the MVP.

Pause rules:

- `。`: 0.25 seconds.
- `、`: 0.12 seconds.
- Speaker change: add about 0.15 seconds.
- Segment end: add about 0.60 seconds and then clear `message_box`.

## Suggested implementation commits

1. Add planning and ignore private refs.
2. Add project skeleton and configuration loading.
3. Add prompt builder that reads `./refs/sucrose.txt` and `./refs/dori.txt`.
4. Add Irodori emoji table and output schema validation.
5. Add SQLite repository and article/idle-topic schema.
6. Add Yahoo RSS parser.
7. Add Yahoo article extractor with `記事全文を読む` handling.
8. Add news candidate deduplication.
9. Add vLLM client and prompt warmup.
10. Add segment generator for news.
11. Add idle-talk segment generator.
12. Add pytchat event provider and Super Chat normalization.
13. Add Program Director and segment queues.
14. Add Irodori-TTS client wrapper.
15. Add obs-websocket `message_box` updater.
16. Add sequential playback with one-chunk prefetch.
17. Add tests for prompt prefix stability.
18. Add tests for Yahoo RSS/article extraction using fixtures.
19. Add tests for chunk validation and emoji repair.
20. Add tests for Super Chat after-news scheduling.
21. Add end-to-end fake-provider smoke test.

## Testing plan

Use fake providers before real external services:

- Fake RSS fixture.
- Fake article HTML fixture with and without `記事全文を読む`.
- Fake vLLM output.
- Fake Irodori-TTS that returns short WAV files or mocked paths.
- Fake obs-websocket client that records `display_text` updates.
- In-memory SQLite for unit tests.

Key tests:

- Fixed prompt is always the prefix.
- Variable payload never appears before the fixed prefix.
- `./refs/` is ignored and not required for unit tests using fixtures.
- RSS parser extracts 8 item links.
- Article extractor follows `記事全文を読む`.
- Body extractor collects multiple `p` paragraphs.
- Duplicate URLs are not reinserted.
- News segment does not get interrupted by Super Chat.
- Super Chat is scheduled after a news segment.
- Every `tts_text` begins with an allowed Irodori emoji.
- OBS receives only `display_text`.
- One-chunk prefetch plays chunks in order.
