import os
import re
import io
import zipfile
import streamlit as st
import fitz  # PyMuPDF
import pykakasi


# ===== ページ設定 =====
st.set_page_config(
    page_title="にじいろくれよん PDF変換",
    page_icon="🌈",
    layout="centered",
)


# =============================================================
#  パスワード認証
# =============================================================

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("""
    <style>
    
    .stApp {
        background: #f8f9fa !important;
    }
    .login-wrap {
        max-width: 360px;
        margin: 80px auto 0 auto;
        text-align: center;
    }
    .login-mark {
        font-size: 2.4em;
        margin-bottom: 12px;
    }
    .login-name {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif;
        font-weight: 400;
        font-size: 1.3em;
        color: #222;
        margin-bottom: 4px;
    }
    .login-sub {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif;
        font-weight: 400;
        font-size: 0.85em;
        color: #9b9a97;
        margin-bottom: 28px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrap">
        <div class="login-mark">🌈</div>
        <div class="login-name">にじいろくれよん</div>
        <div class="login-sub">PDF → PNG 変換ツール</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        correct_password = st.secrets["password"]
    except Exception:
        correct_password = "nijiiro2026"

    password = st.text_input(
        "パスワード",
        type="password",
        placeholder="パスワードを入力",
    )

    if st.button("ログイン", type="primary", use_container_width=True):
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")

    return False


if not check_password():
    st.stop()


# =============================================================
#  CSS — シンプル・高視認性・アクセシブル
# =============================================================
st.markdown("""
<style>


/* === 基本 === */
.stApp {
    background: #f8f9fa !important;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif !important;
    color: #37352f;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    letter-spacing: 0.01em;
    line-height: 1.7;
}

/* === ヘッダー === */
.app-header {
    background: #fff;
    border-bottom: 1px solid #e0dfdc;
    border-radius: 0;
    padding: 24px 28px;
    margin-bottom: 28px;
}
.app-header-top {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
}
.app-header-top span.icon {
    font-size: 1.5em;
}
.app-header-top h1 {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif !important;
    font-weight: 400 !important;
    font-size: 1.25em !important;
    color: #37352f !important;
    margin: 0 !important;
    line-height: 1.3;
}
.app-header-desc {
    font-size: 0.88em;
    color: #787774;
    line-height: 1.5;
}

/* === セクション見出し === */
.sec {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif;
    font-weight: 400;
    font-size: 0.92em;
    color: #37352f;
    padding: 10px 0 6px 0;
    margin-top: 20px;
    border-bottom: 1px solid #e0dfdc;
    display: flex;
    align-items: center;
    gap: 8px;
    letter-spacing: 0.02em;
}

/* === アップロード === */
[data-testid="stFileUploader"] {
    background: #fff !important;
    border: 2px dashed #bbb !important;
    border-radius: 8px !important;
    padding: 8px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #666 !important;
}

/* === ボタン共通 === */
.stButton > button, .stDownloadButton > button {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif !important;
    font-weight: 400 !important;
    border-radius: 6px !important;
    padding: 10px 20px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    opacity: 0.85 !important;
}

/* プライマリ */
.stButton > button[kind="primary"] {
    background: #111 !important;
    color: #fff !important;
    letter-spacing: 0.04em;
    border: none !important;
    font-size: 1em !important;
}

/* ダウンロード */
.stDownloadButton > button {
    background: #0d6efd !important;
    color: #fff !important;
    letter-spacing: 0.04em;
    border: none !important;
}

/* === サイドバー === */
[data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #e0e0e0 !important;
}

.sb-title {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif;
    font-weight: 400;
    font-size: 1em;
    color: #37352f;
    padding-bottom: 8px;
    margin-bottom: 12px;
    border-bottom: 1px solid #e0dfdc;
}
.sb-section {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', 'Meiryo', sans-serif;
    font-weight: 400;
    font-size: 0.82em;
    color: #787774;
    margin: 18px 0 6px 0;
    letter-spacing: 0.04em;
}

/* 登録済みタグ */
.tag {
    display: inline-block;
    background: #f0f0f0;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 4px 10px;
    margin: 2px;
    font-size: 0.85em;
    color: #333;
}

/* === Expander === */
[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid #ddd !important;
    border-radius: 6px !important;
    margin-bottom: 6px !important;
}

/* === 情報カード === */
.info-row {
    display: flex;
    gap: 10px;
    margin: 12px 0 16px 0;
}
.info-card {
    flex: 1;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 14px;
    text-align: center;
}
.info-val {
    font-weight: 400;
    font-size: 1.3em;
    color: #37352f;
}
.info-lbl {
    font-size: 0.75em;
    color: #9b9a97;
    margin-top: 2px;
}

/* === フッター === */
.ft {
    text-align: center;
    padding: 28px 0 12px 0;
    font-size: 0.75em;
    color: #b4b4b0;
    border-top: 1px solid #e0dfdc;
    margin-top: 32px;
}

/* === ログアウト === */
.lo button {
    background: transparent !important;
    color: #aaa !important;
    border: 1px solid #ddd !important;
    font-size: 0.8em !important;
}
</style>
""", unsafe_allow_html=True)


# ===== 読み対応表 =====

def load_kana_map():
    if "kana_map" not in st.session_state:
        st.session_state.kana_map = {}
    return st.session_state.kana_map


def get_kana_prefix(text, kana_map=None):
    if not text:
        return ""
    name_clean = text.replace(" ", "").replace("\u3000", "")
    if kana_map:
        for surname, reading in kana_map.items():
            surname_clean = surname.replace(" ", "").replace("\u3000", "")
            if name_clean.startswith(surname_clean):
                if reading:
                    return reading[0] + "ー"
    kks = pykakasi.kakasi()
    first_char = name_clean[0]
    result = kks.convert(first_char)
    if result:
        kana = result[0]["hira"]
        if kana:
            return kana[0] + "ー"
    return ""


# ===== PDF処理 =====

def extract_info_from_page(page):
    text = page.get_text("text")
    lines = text.split("\n")
    extracted_name = ""
    extracted_date = ""
    extracted_amount = "0円"

    for line in lines:
        clean_line = line.strip()
        if "様分" in clean_line:
            extracted_name = clean_line.replace("様分", "").strip()
            break
    if not extracted_name:
        for line in lines[:15]:
            clean_line = line.strip()
            if clean_line.endswith("様") and "様分" not in clean_line:
                extracted_name = clean_line.replace("様", "").strip()
                break

    match_date = re.search(r"(令和\d+年\d+月)", text)
    if match_date:
        extracted_date = match_date.group(1)
    else:
        match_date_western = re.search(r"(\d{4}年\d+月)", text)
        if match_date_western:
            extracted_date = match_date_western.group(1)

    amount_candidate = ""
    found_amount_label = False
    for line in lines:
        if "御請求金額" in line:
            found_amount_label = True
            match_price = re.search(r"([\d,]+円)", line)
            if match_price:
                amount_candidate = match_price.group(1)
                break
        elif found_amount_label:
            match_price = re.search(r"([\d,]+円)", line)
            if match_price:
                amount_candidate = match_price.group(1)
                break
    if amount_candidate:
        extracted_amount = amount_candidate
    else:
        all_prices = re.findall(r"([\d,]+円)", text)
        if all_prices:
            extracted_amount = all_prices[-1]

    return {
        "name": extracted_name,
        "date": extracted_date,
        "amount": extracted_amount,
    }


def generate_filename(info, fallback_name, page_num, kana_map=None):
    if info["name"]:
        date_str = info["date"] if info["date"] else "日付不明"
        name_clean = info["name"].replace(" ", "").replace("\u3000", "")
        prefix = get_kana_prefix(name_clean, kana_map)
        fname = "利用料請求書）" + prefix + info["name"]
        fname = fname + "（" + date_str + "、" + info["amount"] + "）.png"
        return fname
    else:
        return fallback_name + "_page" + str(page_num + 1) + ".png"


def process_pdfs(uploaded_files, kana_map):
    results = []
    for uploaded_file in uploaded_files:
        try:
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            fallback_name = os.path.splitext(uploaded_file.name)[0]
            for page_num, page in enumerate(doc):
                info = extract_info_from_page(page)
                filename = generate_filename(
                    info, fallback_name, page_num, kana_map
                )
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                png_bytes = pix.tobytes("png")
                results.append({
                    "filename": filename,
                    "png_bytes": png_bytes,
                    "name": info["name"],
                    "date": info["date"],
                    "amount": info["amount"],
                    "status": "ok",
                })
            doc.close()
        except Exception as e:
            results.append({
                "filename": uploaded_file.name,
                "png_bytes": None,
                "name": "",
                "date": "",
                "amount": "",
                "status": "error: " + str(e),
            })
    return results


def create_zip(results):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in results:
            if item["png_bytes"]:
                zf.writestr(item["filename"], item["png_bytes"])
    zip_buffer.seek(0)
    return zip_buffer


# ===================================================================
#  UI
# ===================================================================

# --- ヘッダー ---
st.markdown("""
<div class="app-header">
    <div class="app-header-top">
        <span class="icon">🌈</span>
        <h1>にじいろくれよん PDF → PNG 変換</h1>
    </div>
    <div class="app-header-desc">
        利用料請求書PDFをアップロード → ひらがなプレフィックス付きPNG画像に変換
    </div>
</div>
""", unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown(
        '<div class="sb-title">📝 読み対応表</div>',
        unsafe_allow_html=True,
    )

    kana_map = load_kana_map()

    # CSV一括登録
    st.markdown(
        '<div class="sb-section">CSV から一括登録</div>',
        unsafe_allow_html=True,
    )
    st.caption("A列：名前、B列：読み（ヘッダー行あり）")
    csv_file = st.file_uploader(
        "CSVファイル", type=["csv"], label_visibility="collapsed"
    )
    if csv_file:
        import csv
        content = csv_file.read().decode("utf-8-sig")
        reader = csv.reader(content.splitlines())
        next(reader, None)
        count = 0
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                st.session_state.kana_map[row[0].strip()] = row[1].strip()
                count += 1
        if count > 0:
            st.success(str(count) + " 件登録しました")

    # 手動追加
    st.markdown(
        '<div class="sb-section">手動で追加</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("名前", placeholder="植田")
    with col2:
        new_reading = st.text_input("読み", placeholder="うえだ")
    if st.button("追加", use_container_width=True):
        if new_name and new_reading:
            st.session_state.kana_map[new_name] = new_reading
            st.success(new_name + " → " + new_reading)
            st.rerun()

    # 登録済み
    if kana_map:
        st.markdown(
            '<div class="sb-section">登録済み（'
            + str(len(kana_map)) + ' 件）</div>',
            unsafe_allow_html=True,
        )
        for name, reading in sorted(kana_map.items()):
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(
                '<div class="tag">' + name + ' → ' + reading + '</div>',
                unsafe_allow_html=True,
            )
            if col_b.button("✕", key="del_" + name):
                del st.session_state.kana_map[name]
                st.rerun()

        if st.button("全てクリア", type="secondary"):
            st.session_state.kana_map = {}
            st.rerun()

    # ログアウト
    st.divider()
    st.markdown('<div class="lo">', unsafe_allow_html=True)
    if st.button("ログアウト", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- メイン ---

st.markdown(
    '<div class="sec">📁 PDFをアップロード</div>',
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "PDFファイルを選択（複数可）",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    file_count = len(uploaded_files)
    total_kb = sum(f.size for f in uploaded_files) / 1024

    st.markdown(
        '<div class="info-row">'
        + '<div class="info-card">'
        + '<div class="info-val">' + str(file_count) + '</div>'
        + '<div class="info-lbl">ファイル</div></div>'
        + '<div class="info-card">'
        + '<div class="info-val">' + str(round(total_kb)) + ' KB</div>'
        + '<div class="info-lbl">合計サイズ</div></div>'
        + '</div>',
        unsafe_allow_html=True,
    )

    if st.button("変換を実行", type="primary", use_container_width=True):
        kana_map = load_kana_map()

        with st.spinner("変換中..."):
            results = process_pdfs(uploaded_files, kana_map)

        ok = [r for r in results if r["status"] == "ok"]
        ng = [r for r in results if r["status"] != "ok"]

        if ok:
            st.success(str(len(ok)) + " 枚の画像を生成しました")

            st.markdown(
                '<div class="sec">📥 ダウンロード</div>',
                unsafe_allow_html=True,
            )

            zip_data = create_zip(results)
            st.download_button(
                label="ZIPでまとめてダウンロード",
                data=zip_data,
                file_name="converted_images.zip",
                mime="application/zip",
                use_container_width=True,
            )

            st.markdown(
                '<div class="sec">🖼 変換結果</div>',
                unsafe_allow_html=True,
            )

            for item in ok:
                with st.expander(item["filename"]):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.write("**名前:** " + item["name"])
                        st.write("**日付:** " + item["date"])
                        st.write("**金額:** " + item["amount"])
                    with c2:
                        st.image(item["png_bytes"], width=280)
                    st.download_button(
                        label="この画像をダウンロード",
                        data=item["png_bytes"],
                        file_name=item["filename"],
                        mime="image/png",
                        key="dl_" + item["filename"],
                    )

        if ng:
            st.error(str(len(ng)) + " 件のエラー")
            for item in ng:
                st.warning(item["filename"] + ": " + item["status"])

# --- フッター ---
st.markdown(
    '<div class="ft">にじいろくれよん株式会社 &copy; 2026</div>',
    unsafe_allow_html=True,
)
