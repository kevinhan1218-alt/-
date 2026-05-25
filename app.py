
import streamlit as st
import fitz
from PyPDF2 import PdfReader, PdfWriter
import re
import tempfile
from PIL import Image
import pytesseract

st.set_page_config(page_title="PDF章节提取器", layout="centered")

st.title("📚 PDF章节提取器")
st.write("上传教材 PDF，输入章节名，例如：第五章")

uploaded_file = st.file_uploader("上传 PDF", type=["pdf"])

chapter_input = st.text_input("请输入章节名", placeholder="例如：第五章")

use_ocr = st.checkbox("扫描版 PDF 使用 OCR（推荐）", value=True)

def extract_text_from_page(page, use_ocr=False):
    text = page.get_text()

    if text.strip():
        return text

    if use_ocr:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        ocr_text = pytesseract.image_to_string(img, lang="chi_sim")
        return ocr_text

    return ""

if uploaded_file and chapter_input:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = tmp.name

    doc = fitz.open(pdf_path)

    chapters = {}

    progress = st.progress(0)

    for page_num in range(len(doc)):
        page = doc[page_num]

        text = extract_text_from_page(page, use_ocr)

        match = re.search(r"第([一二三四五六七八九十百0-9]+)章", text)

        if match:
            chapter_name = match.group(0)

            if chapter_name not in chapters:
                chapters[chapter_name] = page_num + 1

        progress.progress((page_num + 1) / len(doc))

    st.subheader("识别到的章节")
    st.write(chapters)

    if chapter_input not in chapters:
        st.error("没有找到该章节")
    else:
        start_page = chapters[chapter_input]

        chapter_pages = sorted(chapters.items(), key=lambda x: x[1])

        end_page = len(doc)

        for i in range(len(chapter_pages)):
            if chapter_pages[i][0] == chapter_input:
                if i + 1 < len(chapter_pages):
                    end_page = chapter_pages[i + 1][1] - 1
                break

        st.success(f"提取页码：{start_page} - {end_page}")

        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for p in range(start_page - 1, end_page):
            writer.add_page(reader.pages[p])

        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

        with open(output_path, "wb") as f:
            writer.write(f)

        with open(output_path, "rb") as f:
            st.download_button(
                label="📥 下载章节 PDF",
                data=f,
                file_name=f"{chapter_input}.pdf",
                mime="application/pdf"
            )
