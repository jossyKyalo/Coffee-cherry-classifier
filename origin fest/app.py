import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
import cv2
import base64

# Load the model
model = tf.keras.models.load_model('coffee_cherry_classifier.h5')

# Function to add a background image
def add_bg_from_url():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("background.webp");
             background-size: cover;
              background-position: center;
             font-family: Arial, sans-serif;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

# Call the function to add background
add_bg_from_url()

# Define a function to load and preprocess an image
def load_image(uploaded_file):
    img = Image.open(uploaded_file)  # Use PIL to open the image
    img = img.resize((64, 64))       # Resize the image to the expected size
    img = np.array(img) / 255.0       # Normalize the image
    return img

# Function to measure size and density
def measure_size_and_density(uploaded_file, mass):
    # Read the uploaded file into a bytes object
    bytes_data = uploaded_file.getvalue()

    # Convert the bytes object to a numpy array
    np_array = np.frombuffer(bytes_data, np.uint8)

    # Decode the numpy array into a cv2 image
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    if img is None:
        st.error("Warning: Could not read the uploaded image.")
        return None, None
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply a threshold to binarize the image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Measure sizes (area) of each contour
    sizes = [cv2.contourArea(c) for c in contours]
    
    # Calculate density for each size
    densities = [(mass / size) if size > 0 else 0 for size in sizes]
    
    return sizes, densities

# Create a Streamlit app
st.title("Coffee Cherry Classifier")

# Add a file uploader to the app
uploaded_file = st.file_uploader("Select an image", type=["jpg", "jpeg", "png"])

# Dynamic mass input
mass = st.number_input("Enter the mass of the coffee cherry (in grams)", min_value=0.0, value=5.0)

# Add a button to the app
if st.button("Classify"):
    if uploaded_file is not None:
        # Load and preprocess the uploaded image
        img = load_image(uploaded_file)
        img = np.expand_dims(img, axis=0)  # Add batch dimension

        # Make a prediction using the model
        prediction = model.predict(img)

        # Get the class label with the highest probability
        class_label = np.argmax(prediction)

        classes = ["ripe", "unripe", "defective or overripe or diseased"] 
        st.write(f"Classified as: {classes[class_label]}")

        # Measure size and density
        sizes, densities = measure_size_and_density(uploaded_file, mass)
        st.write(f"Sizes: {sizes}")
        st.write(f"Densities: {densities}")

        # Display the uploaded image
        st.image(img[0], caption='Uploaded Image', use_column_width=True)

        # Provide feedback based on classification
        if class_label == 0:  # Ripe
            st.success("Feedback: The coffee cherry is ripe and ready for harvest!")
        elif class_label == 1:  # Unripe
            st.warning("Feedback: The coffee cherry is not yet ripe. Please wait a few more days.")
        else:  # Defective
            st.error("Feedback: The coffee cherry is defective or overripe. Please discard it.")
    else:
        st.write("Please upload an image to classify.")
