import streamlit as st
import spacy
import re
from collections import defaultdict
from nltk.corpus import wordnet as wn
import nltk

# 必要に応じて WordNet を初回ダウンロード
try:
    wn.synsets("test")
except:
    nltk.download("wordnet")
    nltk.download("omw-1.4")

# --- NLPモデル ---
nlp = spacy.load("en_core_web_sm")

# --- 多言語UI ---
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

# --- 言語切替 ---
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
            left = " ".join(t.text for t in tokens[max(0, i - context_width):i])
            center = token.text
            right = " ".join(t.text for t in tokens[i + 1:i + 1 + context_width])

            # POS & ENTITYフィルタ
            if selected_pos != "ALL" and token.pos_ != selected_pos:
                continue
            if selected_entity != "ALL":
                ent = token.ent_type_ if token.ent_type_ else "O"
                if ent != selected_entity:
                    continue

            results.append((left, center, right, token.pos_, token.ent_type_))

    # --- KWIC結果表示 ---
    if results:
        st.subheader(L["results"])
        for left, center, right, pos, ent in results:
            st.markdown(
                f"... {left} **{center}** {right} ...  \n"
                f"*POS:* `{pos}`  |  *ENTITY:* `{ent if ent else 'None'}`"
            )
    else:
        st.warning(L["no_results"])

    # --- WordNet辞書表示 ---
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
