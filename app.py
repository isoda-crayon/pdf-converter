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
    """パスワード認証。正しければTrueを返す。"""

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # ログイン画面のスタイル
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap');
    .stApp {
        background-color: #faf6ef !important;
    }
    .login-box {
        background: linear-gradient(135deg, #fff5f5 0%, #fff0f5 50%, #f5f0ff 100%);
        border-radius: 16px;
        padding: 40px 32px;
        max-width: 400px;
        margin: 60px auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        text-align: center;
        border-top: 6px solid transparent;
        border-image: linear-gradient(90deg,
            #ff6b6b, #ffa36b, #ffd93d,
            #6bcb77, #4d96ff, #9b72cf, #ff6b9d) 1;
    }
    .login-box h2 {
        font-family: 'Zen Maru Gothic', sans-serif;
        font-weight: 900;
        color: #5a4040;
        margin-bottom: 8px;
    }
    .login-box p {
        font-family: 'Zen Maru Gothic', sans-serif;
        color: #9a7a7a;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-box">
        <h2>🌈 にじいろくれよん</h2>
        <p>PDF → PNG 変換ツール</p>
    </div>
    """, unsafe_allow_html=True)

    # パスワード取得（Streamlit Secrets → フォールバック）
    try:
        correct_password = st.secrets["password"]
    except Exception:
        # secrets未設定の場合のデフォルト（ローカル開発用）
        correct_password = "nijiiro2026"

    password = st.text_input(
        "🔑 パスワードを入力してください",
        type="password",
        placeholder="パスワード",
    )

    if st.button("ログイン", type="primary", use_container_width=True):
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ パスワードが違います")

    return False


# --- 認証チェック ---
if not check_password():
    st.stop()


# =============================================================
#  マスキングテープ風カスタムCSS（認証後に表示）
# =============================================================
st.markdown("""
<style>
/* ===== Google Fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700;900&family=Kosugi+Maru&display=swap');

/* ===== 全体背景 ===== */
.stApp {
    background-color: #faf6ef !important;
    background-image:
        radial-gradient(circle at 20% 50%, rgba(255,182,193,0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(135,206,250,0.08) 0%, transparent 50%),
        radial-gradient(circle at 50% 80%, rgba(255,255,150,0.08) 0%, transparent 50%);
}

/* ===== テキスト全般 ===== */
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    font-family: 'Zen Maru Gothic', 'Kosugi Maru', sans-serif !important;
}

/* ===== ヘッダーバナー ===== */
.tape-header {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 30%, #a8edea 60%, #fed6e3 100%);
    padding: 28px 24px;
    border-radius: 4px;
    margin-bottom: 24px;
    position: relative;
    box-shadow:
        0 2px 8px rgba(0,0,0,0.06),
        inset 0 1px 0 rgba(255,255,255,0.5);
    border-top: 3px solid rgba(255,255,255,0.6);
    border-bottom: 3px solid rgba(0,0,0,0.04);
}
.tape-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        90deg,
        transparent,
        transparent 4px,
        rgba(255,255,255,0.15) 4px,
        rgba(255,255,255,0.15) 5px
    );
    pointer-events: none;
}
.tape-header h1 {
    font-family: 'Zen Maru Gothic', sans-serif !important;
    font-weight: 900 !important;
    font-size: 1.8em !important;
    color: #5a4040 !important;
    margin: 0 !important;
    text-shadow: 1px 1px 0 rgba(255,255,255,0.5);
    letter-spacing: 0.02em;
}
.tape-header p {
    font-family: 'Zen Maru Gothic', sans-serif !important;
    color: #7a5a5a !important;
    margin: 6px 0 0 0 !important;
    font-size: 0.9em !important;
    font-weight: 500;
}

/* ===== マスキングテープ装飾ストリップ ===== */
.tape-strip {
    height: 8px;
    border-radius: 1px;
    margin: 16px 0;
    opacity: 0.7;
    transform: rotate(-0.3deg);
}
.tape-rainbow {
    background: linear-gradient(90deg,
        #ff6b6b 0%, #ffa36b 14%, #ffd93d 28%,
        #6bcb77 42%, #4d96ff 56%, #9b72cf 70%,
        #ff6b9d 84%, #ff6b6b 100%);
}
.tape-pink {
    background: linear-gradient(90deg, #ffb3ba, #ffdfdf, #ffb3ba);
    transform: rotate(0.2deg);
}
.tape-blue {
    background: linear-gradient(90deg, #bae1ff, #e8f4ff, #bae1ff);
    transform: rotate(-0.5deg);
}
.tape-green {
    background: linear-gradient(90deg, #baffc9, #e8ffed, #baffc9);
    transform: rotate(0.3deg);
}
.tape-yellow {
    background: linear-gradient(90deg, #ffffba, #fffde8, #ffffba);
    transform: rotate(-0.2deg);
}

/* ===== アップロードエリア ===== */
[data-testid="stFileUploader"] {
    background: #fffdf7 !important;
    border: 2px dashed #e8c4a0 !important;
    border-radius: 12px !important;
    padding: 8px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #d4a06a !important;
    background: #fff8ec !important;
}

/* ===== ボタン ===== */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #a8edea 100%) !important;
    color: #5a3a3a !important;
    border: none !important;
    font-family: 'Zen Maru Gothic', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.1em !important;
    padding: 12px 24px !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 6px rgba(255,154,158,0.3) !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.05em;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 12px rgba(255,154,158,0.4) !important;
    transform: translateY(-1px);
}

/* ダウンロードボタン */
.stDownloadButton > button {
    background: linear-gradient(135deg, #a8edea 0%, #bae1ff 100%) !important;
    color: #3a5a5a !important;
    border: none !important;
    font-family: 'Zen Maru Gothic', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 6px rgba(168,237,234,0.3) !important;
}

/* ===== サイドバー ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff5f5 0%, #fff0f5 30%, #f5f0ff 60%, #f0f5ff 100%) !important;
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
    background: linear-gradient(90deg,
        #ff6b6b, #ffa36b, #ffd93d,
        #6bcb77, #4d96ff, #9b72cf, #ff6b9d);
}

/* ===== Expander ===== */
[data-testid="stExpander"] {
    background: #fffdf7 !important;
    border: 1px solid #f0e0d0 !important;
    border-radius: 8px !important;
    border-left: 5px solid #ffb3ba !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"]:nth-child(even) {
    border-left-color: #bae1ff !important;
}

/* ===== セクションラベル ===== */
.section-label {
    display: inline-block;
    background: linear-gradient(90deg, #ffb3ba, #ffdfdf);
    padding: 4px 16px;
    border-radius: 2px;
    font-family: 'Zen Maru Gothic', sans-serif;
    font-weight: 700;
    color: #6a4a4a;
    font-size: 0.85em;
    margin: 16px 0 8px 0;
    transform: rotate(-0.5deg);
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    letter-spacing: 0.05em;
}

/* ===== 登録済みアイテム ===== */
.kana-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(90deg, #ffffba, #fffde8);
    padding: 4px 14px;
    border-radius: 2px;
    margin: 3px 4px;
    font-family: 'Zen Maru Gothic', sans-serif;
    font-size: 0.85em;
    color: #6a5a2a;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transform: rotate(-0.3deg);
}

/* ===== フッター ===== */
.tape-footer {
    text-align: center;
    padding: 20px 0 10px 0;
    color: #baa;
    font-size: 0.75em;
    font-family: 'Zen Maru Gothic', sans-serif;
}

/* ===== ログアウトボタン ===== */
.logout-btn button {
    background: transparent !important;
    color: #baa !important;
    border: 1px solid #dcc !important;
    font-size: 0.8em !important;
}
</style>
""", unsafe_allow_html=True)


# ===== 読み対応表の管理 =====

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
#  UI（認証済みユーザーのみ表示）
# ===================================================================

# --- ヘッダー ---
st.markdown("""
<div class="tape-header">
    <h1>🌈 にじいろくれよん PDF → PNG 変換</h1>
    <p>利用料請求書PDFをアップロードすると、ひらがなプレフィックス付きPNG画像に変換します</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="tape-strip tape-rainbow"></div>', unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 5px 0;">
        <span style="font-size:1.6em;">📝</span>
        <span style="font-family:'Zen Maru Gothic',sans-serif; font-weight:700; font-size:1.1em; color:#6a4a5a;">
            読み対応表
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.caption("名前の読みを正しく変換するための対応表です")

    st.markdown('<div class="tape-strip tape-pink"></div>', unsafe_allow_html=True)

    kana_map = load_kana_map()

    # CSVアップロード
    st.markdown(
        '<div class="section-label">📎 CSVから一括登録</div>',
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
        header = next(reader, None)
        count = 0
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                st.session_state.kana_map[row[0].strip()] = row[1].strip()
                count += 1
        if count > 0:
            st.success(str(count) + " 件登録しました")
        csv_file = None

    st.markdown('<div class="tape-strip tape-blue"></div>', unsafe_allow_html=True)

    # 手動追加
    st.markdown(
        '<div class="section-label">✏️ 手動で追加</div>',
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

    st.markdown('<div class="tape-strip tape-green"></div>', unsafe_allow_html=True)

    # 登録済み一覧
    if kana_map:
        st.markdown(
            '<div class="section-label">🏷️ 登録済み（'
            + str(len(kana_map))
            + ' 件）</div>',
            unsafe_allow_html=True,
        )
        for name, reading in sorted(kana_map.items()):
            col_a, col_b, col_c = st.columns([3, 3, 1])
            col_a.markdown(
                '<div class="kana-item">' + name + '</div>',
                unsafe_allow_html=True,
            )
            col_b.markdown(
                '<div class="kana-item">' + reading + '</div>',
                unsafe_allow_html=True,
            )
            if col_c.button("✕", key="del_" + name):
                del st.session_state.kana_map[name]
                st.rerun()

        st.markdown('<div class="tape-strip tape-yellow"></div>', unsafe_allow_html=True)

        if st.button("全てクリア", type="secondary"):
            st.session_state.kana_map = {}
            st.rerun()

    # ログアウト
    st.markdown('<div class="tape-strip tape-rainbow"></div>', unsafe_allow_html=True)
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("🚪 ログアウト", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- メインエリア ---

st.markdown(
    '<div class="section-label">📁 PDFファイルを選んでね</div>',
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "PDFファイルを選択（複数可）",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    st.info("🌈 " + str(len(uploaded_files)) + " 個のPDFが選択されています")

    st.markdown('<div class="tape-strip tape-pink"></div>', unsafe_allow_html=True)

    if st.button("🎨 変換開始", type="primary", use_container_width=True):
        kana_map = load_kana_map()

        with st.spinner("🖍️ くれよんで変換中..."):
            results = process_pdfs(uploaded_files, kana_map)

        success_count = sum(1 for r in results if r["status"] == "ok")
        error_count = sum(1 for r in results if r["status"] != "ok")

        if success_count > 0:
            st.success(
                "🌈 " + str(success_count) + " 枚のPNG画像を生成しました！"
            )

            st.markdown(
                '<div class="tape-strip tape-rainbow"></div>',
                unsafe_allow_html=True,
            )

            zip_data = create_zip(results)
            st.download_button(
                label="📥 ZIPでまとめてダウンロード",
                data=zip_data,
                file_name="converted_images.zip",
                mime="application/zip",
                use_container_width=True,
            )

            st.markdown(
                '<div class="section-label">🖼️ 変換結果</div>',
                unsafe_allow_html=True,
            )

            for item in results:
                if item["status"] == "ok":
                    with st.expander(
                        "✅ " + item["filename"], expanded=False
                    ):
                        col_info, col_preview = st.columns([1, 1])
                        with col_info:
                            st.write("**🏷️ 名前:** " + item["name"])
                            st.write("**📅 日付:** " + item["date"])
                            st.write("**💰 金額:** " + item["amount"])
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
            st.error(str(error_count) + " 件のエラーがありました")
            for item in results:
                if item["status"] != "ok":
                    st.warning(item["filename"] + ": " + item["status"])

# --- フッター ---
st.markdown('<div class="tape-strip tape-rainbow"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tape-footer">'
    + "🌈 にじいろくれよん株式会社 &copy; 2026 "
    + "| つくった人のぬくもりが伝わるツール"
    + "</div>",
    unsafe_allow_html=True,
)
