import os
import re
import io
import zipfile
import streamlit as st
import fitz  # PyMuPDF
import pykakasi


# ===== ページ設定 =====
st.set_page_config(
    page_title="PDF → PNG 変換ツール",
    page_icon="📄",
    layout="centered",
)


# ===== 読み対応表の管理 =====

def load_kana_map():
    """セッションに保存された読み対応表を返す"""
    if "kana_map" not in st.session_state:
        st.session_state.kana_map = {}
    return st.session_state.kana_map


def get_kana_prefix(text, kana_map=None):
    """名前からひらがなプレフィックスを生成"""
    if not text:
        return ""
    name_clean = text.replace(" ", "").replace("\u3000", "")

    # 1. 対応表から検索
    if kana_map:
        for surname, reading in kana_map.items():
            surname_clean = surname.replace(" ", "").replace("\u3000", "")
            if name_clean.startswith(surname_clean):
                if reading:
                    return reading[0] + "ー"

    # 2. pykakasi フォールバック
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
    """PDFファイルを処理してPNG画像のリストを返す"""
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
    """処理結果をZIPにまとめる"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in results:
            if item["png_bytes"]:
                zf.writestr(item["filename"], item["png_bytes"])
    zip_buffer.seek(0)
    return zip_buffer


# ===== UI =====

st.title("📄 利用料請求書 PDF → PNG 変換")
st.caption("PDFをアップロードすると、ひらがなプレフィックス付きPNG画像に変換します")

# --- サイドバー：読み対応表の管理 ---
with st.sidebar:
    st.header("📝 読み対応表")
    st.caption("名前の読みを正しく変換するための対応表です")

    kana_map = load_kana_map()

    # CSVアップロード
    st.subheader("CSVから一括登録")
    st.caption("A列：名前、B列：読み（ヘッダー行あり）")
    csv_file = st.file_uploader(
        "CSVファイル", type=["csv"], label_visibility="collapsed"
    )
    if csv_file:
        import csv
        content = csv_file.read().decode("utf-8-sig")
        reader = csv.reader(content.splitlines())
        header = next(reader, None)  # ヘッダーをスキップ
        count = 0
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                st.session_state.kana_map[row[0].strip()] = row[1].strip()
                count += 1
        if count > 0:
            st.success(str(count) + " 件登録しました")
        csv_file = None

    # 手動追加
    st.subheader("手動で追加")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("名前", placeholder="植田")
    with col2:
        new_reading = st.text_input("読み", placeholder="うえだ")
    if st.button("追加", use_container_width=True):
        if new_name and new_reading:
            st.session_state.kana_map[new_name] = new_reading
            st.success(new_name + " → " + new_reading + " を追加")
            st.rerun()

    # 現在の対応表を表示
    if kana_map:
        st.subheader("登録済み（" + str(len(kana_map)) + " 件）")
        for name, reading in sorted(kana_map.items()):
            col_a, col_b, col_c = st.columns([3, 3, 1])
            col_a.write(name)
            col_b.write(reading)
            if col_c.button("✕", key="del_" + name):
                del st.session_state.kana_map[name]
                st.rerun()

        if st.button("全てクリア", type="secondary"):
            st.session_state.kana_map = {}
            st.rerun()

# --- メインエリア：PDF処理 ---

uploaded_files = st.file_uploader(
    "PDFファイルを選択（複数可）",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.info(str(len(uploaded_files)) + " 個のPDFが選択されています")

    if st.button("🔄 変換開始", type="primary", use_container_width=True):
        kana_map = load_kana_map()

        with st.spinner("変換中..."):
            results = process_pdfs(uploaded_files, kana_map)

        # 結果表示
        success_count = sum(1 for r in results if r["status"] == "ok")
        error_count = sum(1 for r in results if r["status"] != "ok")

        if success_count > 0:
            st.success(str(success_count) + " 枚のPNG画像を生成しました！")

            # ZIPダウンロードボタン
            zip_data = create_zip(results)
            st.download_button(
                label="📥 ZIPでまとめてダウンロード",
                data=zip_data,
                file_name="converted_images.zip",
                mime="application/zip",
                use_container_width=True,
            )

            # 個別の結果
            st.subheader("変換結果")
            for item in results:
                if item["status"] == "ok":
                    with st.expander(
                        "✅ " + item["filename"], expanded=False
                    ):
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
                        # 個別ダウンロード
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