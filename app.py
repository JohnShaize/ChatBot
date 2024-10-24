import streamlit as st
from langchain_ollama import ChatOllama
import speech_recognition as sr
from PIL import Image
import pytesseract
import io

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Change this path accordingly

# Load custom CSS
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

st.sidebar.image("images/logo.png")
st.title('Welcome To Hush - AI')
st.write("Welcome to your smart assistant, a chatbot dedicated to crafting meaningful conversations and providing insightful answers, all with a strong commitment to your privacy. Got an image with text? Just upload it, and I’ll help you extract the information in no time!")

# Initialize session state for chat histories
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "current_session" not in st.session_state:
    # Create the default session as "General Chat"
    st.session_state.current_session = "General Chat"
    st.session_state.chat_sessions[st.session_state.current_session] = []  # Initialize chat history for the default session

def create_new_chat():
    session_name = st.session_state.new_session_name.strip()  # Get the input name from session state
    if session_name and session_name not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[session_name] = []  # Initialize a new chat history
        st.session_state.current_session = session_name  # Switch to the new session
        st.success(f"New chat session '{session_name}' created!")
    elif session_name in st.session_state.chat_sessions:
        st.error(f"Session '{session_name}' already exists. Please choose a different name.")

# Option to create a new chat
st.sidebar.text_input("Enter session name:", key="new_session_name")  # Input field with unique key
if st.sidebar.button("Create Chat"):
    create_new_chat()

# Sidebar for session management
st.sidebar.header("Chat Sessions")
# Show existing sessions
for session in st.session_state.chat_sessions.keys():
    if st.sidebar.button(session):
        st.session_state.current_session = session



# Display the current session name at the top of the main section
st.header(st.session_state.current_session)

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak now")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        st.info("Processing your audio...")
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("Could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None

uploaded_images = st.file_uploader("Upload images to Extract Text", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# Initialize user input state
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Main section for input options
# Removed duplicate session header here

# Function to process the uploaded images
def process_uploaded_images(uploaded_images):
    extracted_texts = []
    for uploaded_image in uploaded_images:
        image = Image.open(uploaded_image)
        st.image(image, caption='Uploaded Image', use_column_width=True)
        try:
            with st.spinner('Extracting text from the image...'):
                extracted_text = pytesseract.image_to_string(image)
                extracted_texts.append(extracted_text)
                st.write("Extracted Text:")
                st.write(extracted_text)
        except Exception as e:
            st.error(f"An error occurred during text extraction: {e}")
    return extracted_texts

# Analyze images if uploaded
if uploaded_images:
    process_uploaded_images(uploaded_images)

# Add speech input button in the main section
if st.button('Speak to Chatbot'):
    with st.spinner('Listening and processing your speech...'):
        user_input = recognize_speech()
        if user_input:
            st.session_state.user_input = user_input  # Set recognized speech to the input state
            st.rerun()   # Refresh the app to show the updated input

# Form for user input
with st.form("llm-form"):
    text = st.text_area("Enter your question or statement", value=st.session_state.user_input)
    submit = st.form_submit_button("Submit")

def generate_response(input_text):
    # Prepare the context from previous inputs
    context = "\n".join([f"User: {entry['user']}\nAssistant: {entry['ollama']}" for entry in st.session_state.chat_sessions[st.session_state.current_session]])
    context += f"\nUser: {input_text}\nAssistant:"
    
    model = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434/")
    response = model.invoke(context)
    return response.content

if submit and text.strip():  # Check if the text is not empty
    with st.spinner('Generating response...'):
        response = generate_response(text)
        
        # Store the interaction in the current session's chat history
        st.session_state.chat_sessions[st.session_state.current_session].append({'user': text, 'ollama': response})
        st.session_state.user_input = ""  # Clear the input after submission

# Clear chat history button
if st.button('Clear Chat History'):
    st.session_state.chat_sessions[st.session_state.current_session].clear()
    st.success("Chat history cleared!")

# Main section to display chat history and add download functionality
if st.session_state.chat_sessions[st.session_state.current_session]:
    st.write('## Chat History 💬')

    # Display chat history
    for chat in reversed(st.session_state.chat_sessions[st.session_state.current_session]):
        st.write(f"🧑 **User:** {chat['user']}")
        st.write(f"🧠 **Assistant:** {chat['ollama']}")
        st.write('---')
    
    # Function to generate chat history as text
    def get_chat_history_as_text():
        chat_history = st.session_state.chat_sessions[st.session_state.current_session]
        chat_text = "\n".join([f"User: {chat['user']}\nAssistant: {chat['ollama']}\n" for chat in chat_history])
        return chat_text
    
    # Get chat history text for download
    chat_history_text = get_chat_history_as_text()

    # Download button in the main section, below the chat history
    st.download_button(
        label="Download Chat History",
        data=chat_history_text,
        file_name=f"{st.session_state.current_session}_chat_history.txt",
        mime="text/plain"
    )
