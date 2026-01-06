import streamlit as st
import os
import tempfile
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

def main():
    st.title("📄 Universal Document Reader")
    st.markdown("Upload your documents (Word, Excel, PPT, PDF, HTML) to convert them into clean Markdown text.")

    # --- [2] The Interface: Upload Area ---
    uploaded_files = st.file_uploader(
        "Drag and drop files here", 
        accept_multiple_files=True,
        type=['docx', 'xlsx', 'pptx', 'pdf', 'html', 'txt', 'csv', 'json']
    )

    if uploaded_files:
        st.divider()
        st.subheader("Processed Documents")

        # Initialize the Engine
        # Note: MarkItDown handles format detection automatically based on file extension
        md = MarkItDown()

        for uploaded_file in uploaded_files:
            # Create a container for each file to keep UI organized
            with st.container():
                process_file(uploaded_file, md)
                st.divider()

def process_file(uploaded_file, md_engine):
    """
    Handles the logic of saving the upload temporarily, 
    converting it, and cleaning up.
    """
    # Get the original filename and extension
    original_filename = uploaded_file.name
    filename_no_ext, _ = os.path.splitext(original_filename)
    
    # We need a temporary file because MarkItDown expects a file path, 
    # not a memory stream.
    try:
        # Create a temp file with the correct suffix so MarkItDown knows how to treat it
        suffix = os.path.splitext(original_filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # --- [1] The Engine: Conversion ---
        # We perform the conversion
        result = md_engine.convert(tmp_file_path)
        
        # Extract content
        text_content = result.text_content
        
        # --- [2] The Interface: Instant Preview ---
        st.success(f"✅ Successfully converted: **{original_filename}**")
        
        # Display text in a scrollable box
        st.text_area(
            label=f"Preview: {original_filename}",
            value=text_content,
            height=300
        )

        # --- [2] The Interface: Download Options ---
        col1, col2 = st.columns(2)
        
        # Option 1: Download as Markdown (.md)
        new_filename_md = f"{filename_no_ext}_converted.md"
        with col1:
            st.download_button(
                label="⬇️ Download Markdown",
                data=text_content,
                file_name=new_filename_md,
                mime="text/markdown"
            )

        # Option 2: Download as Text (.txt)
        new_filename_txt = f"{filename_no_ext}_converted.txt"
        with col2:
            st.download_button(
                label="⬇️ Download Text File",
                data=text_content,
                file_name=new_filename_txt,
                mime="text/plain"
            )

    except Exception as e:
        # --- [3] Resilience: Error Handling ---
        # Catching all exceptions to prevent app crash
        st.error(f"⚠️ Could not read {original_filename}. Please check the format.")
        # Optional: Print the actual error to console for developer debugging
        print(f"Error processing {original_filename}: {e}")

    finally:
        # Cleanup: Remove the temporary file to keep the server clean
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

if __name__ == "__main__":
    main()
