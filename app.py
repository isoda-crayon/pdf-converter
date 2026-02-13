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

    # ログイン画面
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 40%, #16213e 100%) !important;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(ellipse at 20% 50%, rgba(120,119,198,0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(255,107,107,0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(72,219,251,0.08) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 50vh;
        padding: 40px 20px;
    }
    .login-logo {
        font-size: 3em;
        margin-bottom: 8px;
    }
    .login-title {
        font-family: 'Noto Sans JP', sans-serif;
        font-weight: 900;
        font-size: 1.6em;
        background: linear-gradient(135deg, #ff6b6b, #ffa36b, #ffd93d, #6bcb77, #4d96ff, #9b72cf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
        letter-spacing: 0.02em;
    }
    .login-subtitle {
        font-family: 'Noto Sans JP', sans-serif;
        font-weight: 300;
        color: rgba(255,255,255,0.4);
        font-size: 0.85em;
        letter-spacing: 0.15em;
    }
    .login-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 40px 36px;
        margin-top: 32px;
        width: 100%;
        max-width: 380px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .login-card label {
        color: rgba(255,255,255,0.5) !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        font-size: 0.8em !important;
        letter-spacing: 0.05em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-container">
        <div class="login-logo">🌈</div>
        <div class="login-title">にじいろくれよん</div>
        <div class="login-subtitle">PDF CONVERTER</div>
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
#  モダンデザイン CSS
# =============================================================
st.markdown("""
<style>
/* ===== Fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

/* ===== 全体 ===== */
.stApp {
    background: #fafbfe !important;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    font-family: 'Noto Sans JP', 'Inter', sans-serif !important;
}

/* ===== ヒーローヘッダー ===== */
.hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px;
    padding: 44px 36px 40px 36px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 40px rgba(15,15,26,0.2);
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%; right: -30%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(120,119,198,0.25) 0%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -40%; left: -20%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(72,219,251,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero-rainbow {
    height: 3px;
    background: linear-gradient(90deg, #ff6b6b, #ffa36b, #ffd93d, #6bcb77, #4d96ff, #9b72cf, #ff6b9d);
    border-radius: 2px;
    margin-bottom: 20px;
    opacity: 0.8;
}
.hero-icon {
    font-size: 2.2em;
    margin-bottom: 4px;
}
.hero h1 {
    font-family: 'Noto Sans JP', sans-serif !important;
    font-weight: 900 !important;
    font-size: 1.7em !important;
    color: #fff !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: 0.01em;
    position: relative;
    z-index: 1;
}
.hero-desc {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 300;
    color: rgba(255,255,255,0.55);
    font-size: 0.88em;
    letter-spacing: 0.04em;
    position: relative;
    z-index: 1;
    line-height: 1.6;
}

/* ===== セクション ===== */
.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 14px 0;
}
.section-title-icon {
    width: 32px;
    height: 32px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95em;
    flex-shrink: 0;
}
.section-title-icon.pink { background: linear-gradient(135deg, #ff6b6b20, #ff6b6b10); }
.section-title-icon.blue { background: linear-gradient(135deg, #4d96ff20, #4d96ff10); }
.section-title-icon.green { background: linear-gradient(135deg, #6bcb7720, #6bcb7710); }
.section-title-text {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 700;
    font-size: 0.95em;
    color: #1a1a2e;
    letter-spacing: 0.02em;
}
.section-title-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #e0e0e8, transparent);
}

/* ===== アップロードエリア ===== */
[data-testid="stFileUploader"] {
    background: #fff !important;
    border: 2px dashed #d8dae5 !important;
    border-radius: 16px !important;
    padding: 12px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #9b72cf !important;
    background: #fafaff !important;
    box-shadow: 0 4px 20px rgba(155,114,207,0.08) !important;
}

/* ===== プライマリボタン ===== */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
    color: #fff !important;
    border: none !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05em !important;
    padding: 14px 24px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(15,15,26,0.2) !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.06em;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 25px rgba(15,15,26,0.35) !important;
    transform: translateY(-2px) !important;
}

/* ===== ダウンロードボタン ===== */
.stDownloadButton > button {
    background: linear-gradient(135deg, #6bcb77 0%, #4d96ff 100%) !important;
    color: #fff !important;
    border: none !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    box-shadow: 0 4px 15px rgba(77,150,255,0.2) !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 6px 25px rgba(77,150,255,0.35) !important;
    transform: translateY(-2px) !important;
}

/* ===== サイドバー ===== */
[data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #f0f0f5 !important;
}

.sidebar-header {
    padding: 16px 0 12px 0;
    border-bottom: 1px solid #f0f0f5;
    margin-bottom: 16px;
}
.sidebar-header-title {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 700;
    font-size: 1em;
    color: #1a1a2e;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sidebar-header-sub {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 300;
    font-size: 0.75em;
    color: #999;
    margin-top: 2px;
    letter-spacing: 0.04em;
}

.sidebar-section {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 600;
    font-size: 0.78em;
    color: #aaa;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 20px 0 8px 0;
}

/* ===== 登録済みタグ ===== */
.kana-tag {
    display: inline-block;
    background: #f5f5fa;
    border: 1px solid #ececf2;
    border-radius: 8px;
    padding: 5px 12px;
    margin: 3px 2px;
    font-family: 'Noto Sans JP', sans-serif;
    font-size: 0.82em;
    font-weight: 500;
    color: #444;
    transition: all 0.2s ease;
}
.kana-tag:hover {
    background: #eeeef5;
    border-color: #d0d0e0;
}
.kana-tag .arrow {
    color: #bbb;
    margin: 0 4px;
}

/* ===== Expander（結果）===== */
[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid #f0f0f5 !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stExpander"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
}

/* ===== アラート ===== */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-family: 'Noto Sans JP', sans-serif !important;
}

/* ===== フッター ===== */
.app-footer {
    text-align: center;
    padding: 32px 0 16px 0;
}
.footer-rainbow {
    height: 2px;
    background: linear-gradient(90deg, #ff6b6b, #ffa36b, #ffd93d, #6bcb77, #4d96ff, #9b72cf, #ff6b9d);
    border-radius: 1px;
    margin-bottom: 16px;
    opacity: 0.5;
}
.footer-text {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 300;
    font-size: 0.72em;
    color: #bbb;
    letter-spacing: 0.08em;
}

/* ===== 統計カード ===== */
.stat-row {
    display: flex;
    gap: 12px;
    margin: 16px 0;
}
.stat-card {
    flex: 1;
    background: #fff;
    border: 1px solid #f0f0f5;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.stat-value {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.4em;
    color: #1a1a2e;
}
.stat-label {
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 400;
    font-size: 0.72em;
    color: #aaa;
    margin-top: 2px;
    letter-spacing: 0.06em;
}

/* ===== ログアウト ===== */
.logout-area {
    padding-top: 12px;
    border-top: 1px solid #f0f0f5;
    margin-top: 20px;
}
.logout-area button {
    background: transparent !important;
    color: #ccc !important;
    border: 1px solid #eee !important;
    font-size: 0.78em !important;
    border-radius: 8px !important;
}
.logout-area button:hover {
    color: #999 !important;
    border-color: #ddd !important;
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

# --- ヒーローヘッダー ---
st.markdown("""
<div class="hero">
    <div class="hero-rainbow"></div>
    <div class="hero-icon">🌈</div>
    <h1>にじいろくれよん PDF → PNG</h1>
    <div class="hero-desc">
        利用料請求書PDFをアップロードすると、ひらがなプレフィックス付きPNG画像に自動変換します
    </div>
</div>
""", unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-header-title">📝 読み対応表</div>
        <div class="sidebar-header-sub">名前の読みを正しく変換するための設定</div>
    </div>
    """, unsafe_allow_html=True)

    kana_map = load_kana_map()

    # CSV一括登録
    st.markdown('<div class="sidebar-section">CSV 一括登録</div>', unsafe_allow_html=True)
    st.caption("A列：名前、B列：読み（ヘッダー行あり）")
    csv_file = st.file_uploader(
        "CSVファイル", type=["csv"], label_visibility="collapsed"
    )
    if csv_file:
        import csv
        content = csv_file.read().decode("utf-8-sig")
        reader = csv.reader(content.splitlines())
        header = next(reader, None)
        count = 0
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                st.session_state.kana_map[row[0].strip()] = row[1].strip()
                count += 1
        if count > 0:
            st.success(str(count) + " 件登録しました")

    # 手動追加
    st.markdown('<div class="sidebar-section">手動追加</div>', unsafe_allow_html=True)
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

    # 登録済み一覧
    if kana_map:
        st.markdown(
            '<div class="sidebar-section">登録済み（'
            + str(len(kana_map)) + '件）</div>',
            unsafe_allow_html=True,
        )
        for name, reading in sorted(kana_map.items()):
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(
                '<div class="kana-tag">'
                + name
                + '<span class="arrow">→</span>'
                + reading
                + '</div>',
                unsafe_allow_html=True,
            )
            if col_b.button("✕", key="del_" + name):
                del st.session_state.kana_map[name]
                st.rerun()

        if st.button("全てクリア", type="secondary"):
            st.session_state.kana_map = {}
            st.rerun()

    # ログアウト
    st.markdown('<div class="logout-area">', unsafe_allow_html=True)
    if st.button("ログアウト", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- メインエリア ---

st.markdown("""
<div class="section-title">
    <div class="section-title-icon pink">📁</div>
    <div class="section-title-text">PDFをアップロード</div>
    <div class="section-title-line"></div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "PDFファイルを選択（複数可）",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    file_count = len(uploaded_files)
    total_size = sum(f.size for f in uploaded_files)
    size_str = str(round(total_size / 1024)) + " KB"

    st.markdown(
        '<div class="stat-row">'
        + '<div class="stat-card">'
        + '<div class="stat-value">' + str(file_count) + '</div>'
        + '<div class="stat-label">ファイル数</div>'
        + '</div>'
        + '<div class="stat-card">'
        + '<div class="stat-value">' + size_str + '</div>'
        + '<div class="stat-label">合計サイズ</div>'
        + '</div>'
        + '</div>',
        unsafe_allow_html=True,
    )

    if st.button("変換を実行", type="primary", use_container_width=True):
        kana_map = load_kana_map()

        with st.spinner("変換中..."):
            results = process_pdfs(uploaded_files, kana_map)

        success_count = sum(1 for r in results if r["status"] == "ok")
        error_count = sum(1 for r in results if r["status"] != "ok")

        if success_count > 0:
            st.success(str(success_count) + " 枚のPNG画像を生成しました")

            st.markdown("""
            <div class="section-title">
                <div class="section-title-icon green">📥</div>
                <div class="section-title-text">ダウンロード</div>
                <div class="section-title-line"></div>
            </div>
            """, unsafe_allow_html=True)

            zip_data = create_zip(results)
            st.download_button(
                label="ZIPでまとめてダウンロード",
                data=zip_data,
                file_name="converted_images.zip",
                mime="application/zip",
                use_container_width=True,
            )

            st.markdown("""
            <div class="section-title">
                <div class="section-title-icon blue">🖼</div>
                <div class="section-title-text">変換結果</div>
                <div class="section-title-line"></div>
            </div>
            """, unsafe_allow_html=True)

            for item in results:
                if item["status"] == "ok":
                    with st.expander(item["filename"], expanded=False):
                        col_info, col_preview = st.columns([1, 1])
                        with col_info:
                            st.write("**名前:** " + item["name"])
                            st.write("**日付:** " + item["date"])
                            st.write("**金額:** " + item["amount"])
                        with col_preview:
                            st.image(
                                item["png_bytes"],
                                caption=item["filename"],
                                width=300,
                            )
                        st.download_button(
                            label="この画像をダウンロード",
                            data=item["png_bytes"],
                            file_name=item["filename"],
                            mime="image/png",
                            key="dl_" + item["filename"],
                        )

        if error_count > 0:
            st.error(str(error_count) + " 件のエラー")
            for item in results:
                if item["status"] != "ok":
                    st.warning(item["filename"] + ": " + item["status"])

# --- フッター ---
st.markdown("""
<div class="app-footer">
    <div class="footer-rainbow"></div>
    <div class="footer-text">にじいろくれよん株式会社 &copy; 2026</div>
</div>
""", unsafe_allow_html=True)
