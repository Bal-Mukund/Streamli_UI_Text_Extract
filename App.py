import streamlit as st
import boto3
from streamlit_lottie import st_lottie

import requests
import json
import uuid
import time
import os

s3 = boto3.client("s3")
# Name of the s3 storage Buckets
FILE_STORAGE_S3_BUCKET_NAME = "file-storage-bucket-for-text-extraction"
TEXT_STORAGE_S3_BUCKET_NAME = "text-storage-bucket-after-text-extraction"

# -------------------------------
# Upload File to S3
# -------------------------------
def upload_file_object(fileobj):
    try:
        # creating Unique ID for each file name
        unique_id = str(uuid.uuid4())
        original_file_name= os.path.basename(fileobj.name)
        s3_key = f"{unique_id}_{original_file_name}"       # creates full name of the file
        content_type= fileobj.type or "application/octet-stream"

        s3.upload_fileobj(
            Fileobj=fileobj,
            Bucket=FILE_STORAGE_S3_BUCKET_NAME,
            Key=s3_key,    # Name of the file
            ExtraArgs= {'ContentType': content_type})  # MIME Type of the File-Object
        return s3_key
    except Exception as e:
        st.error(f"ERROR: {e}")
        return None

# -------------------------------s
# Retrieve Extracted Text from S3
# -------------------------------
def get_extracted_text(file_name, timeout= 100):
    """
    Wait up to timeout for the output text file to appear in the S3 bucket.
    """
    start_time = time.time()  #  gives the number of seconds passed since 1970.
    # """ (current time - start_time) gives the total number of seconds, it has been running since.
    #     if the number of seconds exceeds the timeout (30 seconds) the loop stops"""
    while time.time() - start_time < timeout:   # Runs for 30 seconds. 
        try:
            response = s3.get_object(
                Bucket= TEXT_STORAGE_S3_BUCKET_NAME,
                Key= file_name)
            return response["Body"].read().decode("utf-8")
        except s3.exceptions.NoSuchKey as e:
            time.sleep(2)    # Wait for 2 seconds before trying again
    return None

#--------------------------------
#lottie animation
#--------------------------------
file_animation_url = "https://lottie.host/4d8f7293-ebdd-40df-ac64-046a0f95bf5d/Og3XVZ7MXo.json"
wait_animation_url = "https://lottie.host/9499938a-6540-47c9-bd3e-9fb49bbb4f92/op2Sqy2i5X.json"

def load_animation(animation_url: str):  # animation_url should be always a json url from lottie
    try:
        animation = requests.get(animation_url)
        if animation.status_code != 200:
            st.error(f"Lottie load failed: {animation.status_code}")
            return None
        return animation.json()
    except Exception as e:
        st.error(f"Error loading Lottie: {e}")
        return None

# -------------------------------
# 🎯 Streamlit UI
# -------------------------------
st.title("Text Extractor 🖨")  
st_lottie(load_animation(file_animation_url), height=250)
st.markdown(f"Upload any kind of document (_Image or PDF_) to extract text.")
# File upload drag and drop Menu
uploaded_file = st.file_uploader("Drop your files here",
                                 type= ["jpg","jpeg","pdf","png",'webp'],   # Supported File Formats. 
                                 accept_multiple_files= False,
                                 label_visibility= "visible")

# Checks if User have uploaded any file to the streamlit UI
if uploaded_file is not None:
    if st.button("Extract Text", type="primary"):
        file_key = upload_file_object(fileobj=uploaded_file)
    
        if file_key is not None:    # when file uploaded successfully
            # st.success(f"✅ File Uploaded Successfully")

            # Name of the file to look for inside s3 bucket, that is created after text extraction 
            file_name_to_check = os.path.splitext(file_key)[0] + ".txt"

            # crates a placeholder for the animation.
            animation_placeholder = st.empty()
            # Displaying progress
            with st.spinner("Extracting Text Please Wait ...", show_time=True):
                animation_placeholder = st.empty()
                with animation_placeholder.container():
                    st_lottie(load_animation(wait_animation_url), height=350)    

                extracted_text = get_extracted_text(file_name=file_name_to_check)

                animation_placeholder.empty()  # remove animation after loading

            if extracted_text:  # text extracted Successfully
                st.success(f"✅ Text extracted successfully!")
                # st.text_area("📄 Extracted Text", extracted_text, height=700)
                st.text_area("Extracted_text", extracted_text, height= 300)

            else:
                st.error("❌ Failed to retrieve extracted text")

        else:
            st.error("❌ Failed to upload the file.")
