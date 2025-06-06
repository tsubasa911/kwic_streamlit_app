import streamlit as st
import spacy
import re
from collections import defaultdict
from nltk.corpus import wordnet as wn
import nltk

# WordNet初期化（初回のみ）
try:
    wn.synsets("test")
except:
    nltk.download("wordnet")
    nltk.download("omw-1.4")

# NLPモデル読み込み
nlp = spacy.load("en_core_web_sm")

# --- 多言語対応 ---
LANGS = {
    "en": {
        "title": "KWIC Explorer for English Learners",
        "input_mode": "Input Mode",
        "text_input": "Type or paste English text below:",
        "file_upload": "Or upload a .txt file:",
        "keyword": "Keyword to search",
        "context_width": "Context width (number of words)",
        "pos_filter": "POS Filter",
        "entity_filter": "Entity Filter",
        "search": "Search",
        "no_results": "No matching results found.",
        "results": "KWIC Results",
        "dictionary": "📘 Dictionary Definitions (WordNet)"
    },
    "ja": {
        "title": "英語学習者のためのKWIC検索ツール",
        "input_mode": "入力モード",
        "text_input": "英語の文章を入力してください：",
        "file_upload": "または.txtファイルをアップロード：",
        "keyword": "検索キーワード",
        "context_width": "前後の単語数",
        "pos_filter": "品詞フィルター",
        "entity_filter": "固有表現フィルター",
        "search": "検索する",
        "no_results": "該当する例が見つかりませんでした。",
        "results": "KWIC結果",
        "dictionary": "📘 語義（WordNetより）"
    }
}

# --- 言語設定 ---
lang = st.sidebar.selectbox("Language / 言語", options=["en", "ja"])
L = LANGS[lang]

# --- タイトル表示 ---
st.title(L["title"])

# --- 入力モード ---
input_mode = st.radio(L["input_mode"], ["Text", "File"])
text = ""

if input_mode == "Text":
    text = st.text_area(L["text_input"], height=200)
else:
    uploaded_file = st.file_uploader(L["file_upload"], type=["txt"])
    if uploaded_file is not None:
        text = uploaded_file.read().decode("utf-8")

# --- 検索条件 ---
keyword = st.text_input(L["keyword"])
context_width = st.slider(L["context_width"], 1, 10, 5)
pos_options = ["ALL", "NOUN", "VERB", "ADJ", "ADV"]
entity_options = ["ALL", "PERSON", "ORG", "GPE", "PRODUCT", "DATE"]
selected_pos = st.selectbox(L["pos_filter"], pos_options)
selected_entity = st.selectbox(L["entity_filter"], entity_options)

# --- 検索実行 ---
if st.button(L["search"]) and keyword and text:
    doc = nlp(text)
    tokens = [token for token in doc]
    results = []

    for i, token in enumerate(tokens):
        if token.text.lower() == keyword.lower():
            left = tokens[max(0, i - context_width):i]
            center = token
            right = tokens[i + 1:i + 1 + context_width]

            # フィルタ適用
            if selected_pos != "ALL" and token.pos_ != selected_pos:
                continue
            ent = token.ent_type_ if token.ent_type_ else "None"
            if selected_entity != "ALL" and ent != selected_entity:
                continue

            results.append((left, center, right, token.pos_, ent))

    if results:
        st.subheader(L["results"])
        for idx, (left, center, right, pos, ent) in enumerate(results, 1):
            # 強調表示処理
            right_str = ""
            if right:
                next_token = right[0]
                highlighted_next = (
                    f"<span style='background-color:#fff176; color:#000; font-weight:bold; padding:2px; border-radius:4px;'>"
                    f"{next_token.text}</span>"
                )
                right_rest = " ".join(t.text for t in right[1:])
                right_str = f"{highlighted_next} {right_rest}"

            left_str = " ".join(t.text for t in left)
            center_str = (
                f"<span style='background-color:#64b5f6; font-weight:bold; padding:2px; border-radius:4px;'>"
                f"{center.text}</span>"
            )

            # レスポンシブ対応 + インデックス強調
            st.markdown(
                f"<div style='font-size: 1rem; word-wrap: break-word;'>"
                f"<span style='font-size: 1.25rem; font-weight: bold; margin-right: 8px;'>{idx}.</span>"
                f"... {left_str} {center_str} {right_str} ..."
                f"</div>"
                f"<div style='font-size: 0.85rem; color: gray;'>POS: <code>{pos}</code> &nbsp;|&nbsp; ENTITY: <code>{ent}</code></div><hr>",
                unsafe_allow_html=True
            )
    else:
        st.warning(L["no_results"])

    # --- WordNet定義表示 ---
    if keyword:
        st.subheader(L["dictionary"])
        synsets = wn.synsets(keyword)
        if synsets:
            for i, syn in enumerate(synsets[:5]):
                st.markdown(f"**{i+1}. {syn.name()}**")
                st.write(f"- Definition: {syn.definition()}")
                if syn.examples():
                    st.write(f"- Example: _{syn.examples()[0]}_")
                if syn.lemmas():
                    synonyms = set(lemma.name() for lemma in syn.lemmas())
                    st.write(f"- Synonyms: {', '.join(synonyms)}")
                st.markdown("---")
        else:
            st.info("No definitions found in WordNet.")
