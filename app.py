import streamlit as st
import os
import tempfile
import pdfplumber
from markitdown import MarkItDown

# --- Page Configuration ---
st.set_page_config(
    page_title="Universal Document Reader",
    page_icon="📄",
    layout="centered"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .stTextArea textarea {
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

def format_file_size(size_in_bytes):
    """Helper to convert bytes to KB or MB"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} bytes"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def main():
    st.title("📄 Universal Document Reader")
    st.markdown("Upload your documents (Word, Excel, PPT, PDF, HTML) to convert them into clean Markdown text.")

    # --- Upload Area ---
    uploaded_files = st.file_uploader(
        "Drag and drop files here", 
        accept_multiple_files=True,
        type=['docx', 'xlsx', 'pptx', 'pdf', 'html', 'txt', 'csv', 'json']
    )

    if uploaded_files:
        st.divider()
        st.subheader("Processed Documents")

        md = MarkItDown()

        for uploaded_file in uploaded_files:
            with st.container():
                process_file(uploaded_file, md)
                st.divider()

def process_file(uploaded_file, md_engine):
    original_filename = uploaded_file.name
    filename_no_ext, file_ext = os.path.splitext(original_filename)
    
    # Calculate Original Size
    original_size_bytes = uploaded_file.size
    
    # Create temp file
    tmp_file_path = None
    try:
        suffix = file_ext.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        text_content = ""
        conversion_success = False
        error_details = ""

        # --- Attempt 1: MarkItDown (Primary Engine) ---
        try:
            result = md_engine.convert(tmp_file_path)
            text_content = result.text_content
            conversion_success = True
        except Exception as e:
            error_details += f"MarkItDown failed: {str(e)}\n"
            
            # --- Attempt 2: PDF Fallback (pdfplumber) ---
            if suffix == '.pdf':
                try:
                    with pdfplumber.open(tmp_file_path) as pdf:
                        text_content = "\n\n".join([page.extract_text() or "" for page in pdf.pages])
                    if text_content.strip():
                        conversion_success = True
                        original_filename += " (processed with Fallback Engine)"
                    else:
                        error_details += "Fallback failed: PDF appears empty.\n"
                except Exception as fallback_e:
                    error_details += f"Fallback failed: {str(fallback_e)}\n"

        # --- Success Path ---
        if conversion_success:
            st.success(f"✅ Successfully converted: **{original_filename}**")
            
            # Create Tabs for View Options
            tab1, tab2 = st.tabs(["📄 Preview & Download", "📊 File Size Comparison"])
            
            # --- TAB 1: Preview & Download ---
            with tab1:
                st.text_area(
                    label=f"Preview content",
                    value=text_content,
                    height=300,
                    label_visibility="collapsed"
                )

                col1, col2 = st.columns(2)
                new_filename_md = f"{filename_no_ext}_converted.md"
                with col1:
                    st.download_button(
                        label="⬇️ Download Markdown",
                        data=text_content,
                        file_name=new_filename_md,
                        mime="text/markdown"
                    )

                new_filename_txt = f"{filename_no_ext}_converted.txt"
                with col2:
                    st.download_button(
                        label="⬇️ Download Text File",
                        data=text_content,
                        file_name=new_filename_txt,
                        mime="text/plain"
                    )

            # --- TAB 2: File Size Comparison ---
            with tab2:
                # Calculate Converted Size (approximate bytes of the text string)
                converted_size_bytes = len(text_content.encode('utf-8'))
                
                # Calculate Savings
                if original_size_bytes > 0:
                    savings = (original_size_bytes - converted_size_bytes) / original_size_bytes * 100
                else:
                    savings = 0
                
                # Create Clean Table Data
                data = [
                    {"Metric": "Original File Size", "Value": format_file_size(original_size_bytes)},
                    {"Metric": "Converted Text Size", "Value": format_file_size(converted_size_bytes)}
                ]
                
                # Display Table
                st.table(data)
                
                # Display Highlighted Percentage
                if savings > 0:
                    st.markdown(f"### 📉 Text version is **{savings:.1f}% smaller**.")
                else:
                    st.markdown(f"### 📈 Text version is **{abs(savings):.1f}% larger**.")

        # --- Failure Path ---
        else:
            st.error(f"⚠️ Could not read {original_filename}. Please check the format.")
            with st.expander("See Error Details"):
                st.code(error_details)

    except Exception as e:
        st.error(f"⚠️ System Error processing {original_filename}.")
        print(f"Critical Error: {e}")
    
    finally:
        # Cleanup temp file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except Exception:
                pass

if __name__ == "__main__":
    main()
