import streamlit as st
import pickle
import pandas as pd
import random
import json
import time
import os
from sklearn.preprocessing import StandardScaler
import streamlit.components.v1 as components

# Apply a custom style
st.set_page_config(page_title="Dyslexia Detection Tool", page_icon="🧠", layout="wide")
st.markdown("""
    <style>
    /* Center the content */
    .main > div {{
        max-width: 800px;
        margin: auto;
    }}
    /* Style headers */
    h1, h2, h3 {{
        color: #2c3e50;
        text-align: center;
    }}
    /* Style the countdown timer */
    #timer {{
        font-size: 24px;
        font-weight: bold;
        color: #e74c3c;
        text-align: center;
        margin-bottom: 20px;
    }}
    /* Style buttons */
    .stButton>button {{
        background-color: #2ecc71;
        color: white;
        border: none;
        padding: 10px 20px;
        margin: 5px 0px;
        cursor: pointer;
        font-size: 16px;
        border-radius: 4px;
    }}
    .stButton>button:hover {{
        background-color: #27ae60;
    }}
    /* Style radio buttons */
    .stRadio > label {{
        font-weight: bold;
    }}
    /* Style warnings */
    .stWarning {{
        background-color: #f1c40f;
        color: #2c3e50;
    }}
    /* Style success messages */
    .stSuccess {{
        background-color: #2ecc71;
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

# Load the trained model and scaler
with open('model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('scaler.pkl', 'rb') as scaler_file:
    scaler = pickle.load(scaler_file)

# The exact feature names used during training
columns = ['Language_vocab', 'Memory', 'Speed', 'Visual_discrimination', 'Audio_Discrimination', 'Survey_Score']

# Load vocabulary questions
with open('questions_vocab.json', 'r') as file:
    vocab_data = json.load(file)

# Set the maximum and minimum time limits in minutes
max_time = 30  # Total time for the test in minutes
min_time = 3   # Time at which speed score is at maximum (1)

# Initialize session state variables
if 'start_time' not in st.session_state:
    st.session_state.start_time = int(time.time())  # Store as integer seconds

if 'time_up' not in st.session_state:
    st.session_state.time_up = False

# Function to calculate time remaining
def get_time_remaining():
    elapsed_time = int(time.time()) - st.session_state.start_time
    time_remaining = max(0, max_time * 60 - elapsed_time)
    return time_remaining

# Display the countdown timer using JavaScript
time_remaining = get_time_remaining()

# If time is up, set the flag
if time_remaining <= 0:
    st.session_state.time_up = True

# Function to display the countdown timer
def display_timer():
    total_seconds = get_time_remaining()
    if total_seconds <= 0:
        total_seconds = 0
        st.session_state.time_up = True
    else:
        st.session_state.time_up = False
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    countdown_html = f"""
    <script>
    function startTimer(duration, display) {{
        var timer = duration, minutes, seconds;
        setInterval(function () {{
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;

            display.innerHTML = "⏳ Time Remaining: " + minutes + ":" + seconds;

            if (--timer < 0) {{
                timer = 0;
                display.innerHTML = "⏰ Time is up!";
            }}
        }}, 1000);
    }}

    window.onload = function () {{
        var totalSeconds = {total_seconds};
        var display = document.getElementById('timer');
        startTimer(totalSeconds, display);
    }};
    </script>
    <div id="timer">⏳ Time Remaining: {minutes:02d}:{seconds:02d}</div>
    """

    components.html(countdown_html, height=80)

# Call the function to display the timer
display_timer()

# Streamlit UI
st.title("🧠 Dyslexia Detection Tool")

# Vocabulary Test
st.header("📖 Vocabulary Test")
st.write("Choose the correct word for each sentence:")

# Check if time is up before displaying inputs
if not st.session_state.time_up:
    # Check if the questions have already been selected in the session state
    if 'selected_questions' not in st.session_state:
        # Randomly choose 10 sentence completion questions
        sentence_completion_questions = [q for q in vocab_data['questions'] if q['type'] == 'sentence_completion']
        st.session_state.selected_questions = random.sample(sentence_completion_questions, 10)

    # Get the selected questions from session state
    selected_questions = st.session_state.selected_questions

    # Initialize user answers if not already done
    if 'vocab_user_answers' not in st.session_state:
        st.session_state.vocab_user_answers = ['Select an answer'] * len(selected_questions)

    # Display the questions
    for i, question in enumerate(selected_questions):
        st.markdown(f"<h5>Question {i+1}: {question['question']}</h5>", unsafe_allow_html=True)
        options = ['Select an answer'] + question['options']
        user_answer = st.radio(
            f"Choose the correct answer for Question {i+1}",
            options=options,
            index=options.index(st.session_state.vocab_user_answers[i]) if st.session_state.vocab_user_answers[i] in options else 0,
            key=f"vocab_q{i+1}"
        )
        st.session_state.vocab_user_answers[i] = user_answer

    # Submit button to evaluate the answers
    if st.button("Submit Vocabulary Test"):
        # Collect the correct answers for the selected questions
        correct_answers = [q['correct_answer'] for q in selected_questions]
        # Calculate score, assigning 0 for unanswered questions
        score_count = 0
        for user_answer, correct in zip(st.session_state.vocab_user_answers, correct_answers):
            if user_answer != 'Select an answer' and user_answer.lower() == correct.lower():
                score_count += 1
            # Else, score is 0 for this question
        vocab_score = score_count / len(correct_answers)
        st.success(f"Vocabulary Test Score: {vocab_score:.2f} (0 = no correct answers, 1 = all correct answers)")
        st.session_state.Language_vocab = vocab_score  # Store the score in session state
else:
    st.warning("Time is up! Vocabulary Test is no longer available.")

st.markdown("---")  # Add a horizontal line separator

# Memory Test

# Function to evaluate the memory test for each sequence
def evaluate_memory(user_answer, correct_answer):
    # Compare the entire string (the sequence of digits) without spaces
    return user_answer.strip() == correct_answer.strip()
# Memory Test
st.header("🧩 Memory Test")
st.write("Observe the sequence of numbers. After the sequence disappears, type them in the correct order and press submit to check your answer.")
# Check if the sequences have already been selected in the session state
if 'sequences' not in st.session_state:
    # Generate 5 random sequences of 6 digits
    st.session_state.sequences = [random.sample(range(10), 6) for _ in range(5)]
# Store user answers in session state
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = ['' for _ in range(5)]  # Initialize empty answers for each sequence
# Store scores for each sequence
if 'scores' not in st.session_state:
    st.session_state.scores = [None for _ in range(5)]  # Initialize None for scores to evaluate later
# Store whether each sequence has been displayed or not
if 'displayed' not in st.session_state:
    st.session_state.displayed = [False for _ in range(5)]  # Track if each sequence is displayed
# Store whether each sequence has been submitted or not
if 'submitted' not in st.session_state:
    st.session_state.submitted = [False for _ in range(5)]  # Track if each sequence is submitted
# Display buttons for each sequence
for i in range(5):
    sequence_label = f"Sequence {i + 1}"
    # Display the sequence only if it's not displayed yet and not submitted
    if not st.session_state.displayed[i] and not st.session_state.submitted[i]:
        # Button to display the sequence
        if st.button(f"Display Sequence {i + 1}", key=f"display_{i}"):
            # Show the sequence to the user
            sequence = st.session_state.sequences[i]
            sequence_str = " ".join(map(str, sequence))
            # Display the sequence for 1.5 seconds
            st.write(f"**{sequence_label}:** {sequence_str}")
            time.sleep(1.5)  # Wait for 1.5 seconds
            # Hide the sequence after time has passed
            st.empty()
            # Mark this sequence as displayed
            st.session_state.displayed[i] = True
    # Input box for the user to enter their answer for this sequence
    if st.session_state.displayed[i] and not st.session_state.submitted[i]:
        user_answer = st.text_input(f"Enter the sequence for {sequence_label}", max_chars=6, key=f"sequence_{i}_input", 
                                     value=st.session_state.user_answers[i])  # Preserve previous input
        # Store the user answer in session state for this sequence
        if user_answer:
            st.session_state.user_answers[i] = user_answer.strip()  # Store the entire input as a string
        # Button to submit the answer for this sequence
        if st.button(f"Submit {sequence_label}", key=f"submit_{i}") and not st.session_state.submitted[i]:
            # Evaluate the sequence answer
            if evaluate_memory(user_answer, ''.join(map(str, st.session_state.sequences[i]))):
                st.session_state.scores[i] = 1  # Correct
                st.write(f"**{sequence_label}: Correct!**")
            else:
                st.session_state.scores[i] = 0  # Incorrect
                st.write(f"**{sequence_label}: Incorrect!**")
            # Mark the sequence as submitted
            st.session_state.submitted[i] = True
# Audio-Based Memory Test Section
st.header("Memory Test Part 2: Immediate Recall")
st.write("Listen carefully to the audio. After the audio finishes, type in the words in the correct order and press submit to check your answer.")
# Audio path for the WAV files
audio_path = r"/Users/apple/Downloads/Audios_memory"
# List of audio files based on the path you provided 
st.session_state.audio_files = [
    f"{audio_path}/audio_1.wav",  # Apple, Lettuce, House, River, Dog, Book, Cooking.
    f"{audio_path}/audio_2.wav",  # Dog, Cat, Rabbit, Horse, Sheep, Cow, Goat. (Farm animals)
    f"{audio_path}/audio_3.wav",  # Table, Chair, Sofa, Bed, Desk, Lamp, Shelf. (Furniture)
    f"{audio_path}/audio_4.wav",  # River, Lake, Ocean, Pond, Stream, Beach, Waterfall. (Bodies of water)
    f"{audio_path}/audio_5.wav",  # Red, Blue, Green, Yellow, Pink, Black, White. (Colors)
    f"{audio_path}/audio_6.wav",  # Car, Bus, Train, Plane, Boat, Bike, Truck. (Modes of transport)
    f"{audio_path}/audio_7.wav",  # Rain, Snow, Sun, Cloud, Wind, Storm, Thunder. (Weather)
    f"{audio_path}/audio_8.wav",  # Pen, Pencil, Eraser, Paper, Book, Notebook, Ruler. (Stationery)
    f"{audio_path}/audio_9.wav",  # Tree, Flower, Grass, Leaf, Seed, Branch, Bush. (Nature)
    f"{audio_path}/audio_10.wav"  # Shirt, Pants, Socks, Jacket, Hat, Gloves, Scarf.
]
# Correct answers for each audio file
st.session_state.correct_answers = [
    ["Apple", "Lettuce", "House", "River", "Dog", "Book", "Cooking"],
    ["Dog", "Cat", "Rabbit", "Horse", "Sheep", "Cow", "Goat"],
    ["Table", "Chair", "Sofa", "Bed", "Desk", "Lamp", "Shelf"],
    ["River", "Lake", "Ocean", "Pond", "Stream", "Beach", "Waterfall"],
    ["Red", "Blue", "Green", "Yellow", "Pink", "Black", "White"],
    ["Car", "Bus", "Train", "Plane", "Boat", "Bike", "Truck"],
    ["Rain", "Snow", "Sun", "Cloud", "Wind", "Storm", "Thunder"],
    ["Pen", "Pencil", "Eraser", "Paper", "Book", "Notebook", "Ruler"],
    ["Tree", "Flower", "Grass", "Leaf", "Seed", "Branch", "Bush"],
    ["Shirt", "Pants", "Socks", "Jacket", "Hat", "Gloves", "Scarf"]
]
# Check if the audio selection is already in the session state
if 'selected_audios' not in st.session_state:
    # Randomly select 5 audios from the list of 10
    st.session_state.selected_audios = random.sample(list(enumerate(st.session_state.audio_files)), 5)
# Initialize playback counters for each audio
if 'audio_play_counts' not in st.session_state:
    st.session_state.audio_play_counts = [0 for _ in range(len(st.session_state.selected_audios))]
# Store user answers for audio-based test
if 'audio_user_answers' not in st.session_state:
    st.session_state.audio_user_answers = ['' for _ in range(5)]  # Initialize empty answers
# Store scores for audio test
if 'audio_scores' not in st.session_state:
    st.session_state.audio_scores = [None for _ in range(5)]  # Initialize None for scores
# Function to play audio via Streamlit's native audio function
def play_audio(audio_file):
    st.audio(audio_file, format="audio/wav")
# Display each audio and input field
for idx, (audio_idx, audio_path) in enumerate(st.session_state.selected_audios):
    audio_label = f"Audio {idx + 1}"
    play_count = st.session_state.audio_play_counts[idx]  # Get the current play count
    # Button to play the audio
    if play_count < 2:
        if st.button(f"Play {audio_label} ({2 - play_count} plays left)", key=f"play_{idx}"):
            # Increment the play count
            st.session_state.audio_play_counts[idx] += 1
            play_audio(audio_path)  # Play the audio using Streamlit's audio function
    else:
        st.write(f"**{audio_label}: Audio can no longer be played.**")
    # Input box for the user to enter their answer
    user_answer_audio = st.text_input(f"Enter your answer for {audio_label}", key=f"audio_input_{idx}", 
                                      value=st.session_state.audio_user_answers[idx])
    # Store user answer in session state
    if user_answer_audio:
        st.session_state.audio_user_answers[idx] = user_answer_audio.strip()
    # Button to submit the answer for this audio
    if st.button(f"Submit {audio_label}", key=f"audio_submit_{idx}") and st.session_state.audio_scores[idx] is None:
        # Evaluate the answer
        correct_answer = " ".join(st.session_state.correct_answers[audio_idx])
        if user_answer_audio.lower() == correct_answer.lower():
            st.session_state.audio_scores[idx] = 1  # Correct
            st.write(f"**{audio_label}: Correct!**")
        else:
            st.session_state.audio_scores[idx] = 0  # Incorrect
            st.write(f"**{audio_label}: Incorrect! The correct answer was '{correct_answer}'**")
# Button to calculate final score for audio test
if st.button("Submit Final Audio Test Score"):
    audio_total_score = sum(filter(None, st.session_state.audio_scores))  # Filter out None values
    audio_total_percentage = audio_total_score / len(st.session_state.audio_scores)
    st.write(f"Final Audio Test Score: {audio_total_percentage:.2f} (0 = no correct answers, 1 = all correct answers)")
    # Optionally, display results for each audio
    for idx, (audio_idx, _) in enumerate(st.session_state.selected_audios):
        correct_answer = " ".join(st.session_state.correct_answers[audio_idx])
        st.write(f"Audio {idx + 1}:")
        st.write(f"User Answer: '{st.session_state.audio_user_answers[idx]}'")
        st.write(f"Correct Answer: '{correct_answer}'")
        st.write(f"Score: {st.session_state.audio_scores[idx]}")
# Button to calculate and show final memory score
if st.button("Submit Final Memory Test Score"):
    total_score = sum(st.session_state.scores)  # Add up the scores for all sequences
    total_score_percentage = total_score / 5  # Calculate the percentage (total score / number of sequences)
    st.write(f"Final Memory Test Score: {total_score_percentage:.2f} (0 = no correct answers, 1 = all correct answers)")

st.markdown("---")  # Add a horizontal line separator

# Visual Discrimination Test Section
st.header("👁️ Visual Discrimination Test")
st.write("Complete the tasks below to assess visual discrimination ability.")

if not st.session_state.time_up:
    # Letter Identification
    st.subheader("🔤 Letter Identification")
    st.write("On the following line of letters, count the number of 'd' letters:")
    st.markdown("<div style='font-size:20px; text-align:center; color:#8e44ad;'><strong>`b p q d b d p q b d p q`</strong></div>", unsafe_allow_html=True)

    # Input for Letter Identification
    if 'user_count_d' not in st.session_state:
        st.session_state.user_count_d = 0

    user_count_d = st.number_input(
        "Enter the number of 'd' letters you found:",
        min_value=0, max_value=12, step=1,
        value=st.session_state.user_count_d,
        key="letter_count"
    )
    st.session_state.user_count_d = user_count_d

    # Button to submit Letter Identification task
    if st.button("Submit Letter Identification"):
        correct_count_d = 3  # Correct answer for the number of 'd'
        score_letter_identification = 0
        if user_count_d != 0:
            score_letter_identification = min(user_count_d, correct_count_d) * (1/3)  # Each correct 'd' is worth 0.33, max is 1
        st.success(f"Score for Letter Identification: {score_letter_identification:.2f} / 1")
        st.session_state.score_letter_identification = score_letter_identification  # Store the score

    st.markdown("---")  # Add a horizontal line separator

    # Spot the Differences
    st.subheader("🔎 Spot the Differences")
    st.write("Identify the differences in the following sequence:")
    st.markdown("<div style='font-size:20px; text-align:center; color:#e67e22;'><strong>`b p q d d p`</strong></div>", unsafe_allow_html=True)

    # Pre-defined correct differences
    correct_differences = ["b", "p", "q", "d"]

    # Input for Spot the Differences
    if 'user_spot_diff' not in st.session_state:
        st.session_state.user_spot_diff = ''

    user_spot_diff = st.text_input(
        "List the differences you spotted (separate each with a comma):",
        value=st.session_state.user_spot_diff,
        key="spot_diff"
    )
    st.session_state.user_spot_diff = user_spot_diff

    # Button to submit Spot the Differences task
    if st.button("Submit Spot the Differences"):
        # Process user input
        if user_spot_diff.strip() != '':
            user_differences = [item.strip().lower() for item in user_spot_diff.split(",") if item.strip()]
            unique_user_differences = list(set(user_differences))

            # Identify invalid inputs
            invalid_differences = [diff for diff in unique_user_differences if diff not in correct_differences]

            # Count correct differences
            correct_count = sum(1 for diff in unique_user_differences if diff in correct_differences)

            # Calculate the score
            score_spot_differences = min(correct_count * 0.25, 1)  # Cap the score at 1
        else:
            # No input provided
            score_spot_differences = 0
            unique_user_differences = []
            invalid_differences = []
            correct_count = 0
        # Display the result
        st.write(f"**Your Input:** {user_spot_diff}")
        st.write(f"**Correct Differences:** {', '.join(correct_differences)}")
        st.write(f"**Unique Differences Considered:** {', '.join(unique_user_differences)}")
        if invalid_differences:
            st.warning(f"**Invalid Differences:** {', '.join(invalid_differences)} (not part of the correct differences)")
        st.write(f"**Number of Correct Differences Identified:** {correct_count}")
        st.success(f"Score for Spot the Differences: {score_spot_differences:.2f} / 1")
        st.session_state.score_spot_differences = score_spot_differences  # Store the score

    st.markdown("---")  # Add a horizontal line separator

    # Odd One Out
    st.subheader("🚦 Odd One Out")
    st.write("Choose the option that doesn't belong:")

    # Odd One Out Options
    options = ['Select an answer', "a) ○", "b) ○", "c) ○", "d) ■"]

    # Initialize 'odd_one_out' in session state if not present
    if 'odd_one_out' not in st.session_state:
        st.session_state['odd_one_out'] = 'Select an answer'

    odd_one_out = st.radio(
        "Which is the odd one out?",
        options=options,
        index=options.index(st.session_state['odd_one_out']) if st.session_state['odd_one_out'] in options else 0,
        key="odd_one_out"
    )

    # Button to submit Odd One Out task
    if st.button("Submit Odd One Out"):
        if st.session_state['odd_one_out'] != 'Select an answer':
            correct_answer = "d) ■"
            if st.session_state['odd_one_out'] == correct_answer:
                st.success("Correct! The odd one out is 'd) ■'.")
                score_odd_one_out = 1
            else:
                st.error(f"Incorrect. The correct answer is 'd) ■'. You selected {st.session_state['odd_one_out']}.")
                score_odd_one_out = 0
        else:
            st.warning("No answer selected. Score: 0")
            score_odd_one_out = 0
        st.success(f"Score for Odd One Out: {score_odd_one_out:.2f} / 1")
        st.session_state.score_odd_one_out = score_odd_one_out  # Store the score

    # Button to calculate final Visual Discrimination score
    if st.button("Submit Final Visual Discrimination Score"):
        visual_total_score = (
            st.session_state.get('score_letter_identification', 0) +
            st.session_state.get('score_spot_differences', 0) +
            st.session_state.get('score_odd_one_out', 0)
        ) / 3  # Average the scores
        st.success(f"Final Visual Discrimination Score: {visual_total_score:.2f} (0 = lowest, 1 = highest)")
        st.session_state.Visual_discrimination = visual_total_score  # Store the score in session state
else:
    st.warning("Time is up! Visual Discrimination Test is no longer available.")

st.markdown("---")  # Add a horizontal line separator

# Audio Discrimination Test Section
st.header("🎧 Audio Discrimination Test")
st.write("Complete the tasks below to assess audio discrimination ability.")

if not st.session_state.time_up:
    # Phoneme Discrimination
    st.subheader("🔊 Phoneme Discrimination")
    st.write("Listen to each audio pair and indicate whether they sound the same or different.")

    # Updated file paths and questions
    phoneme_questions = [
        ("Audio 1", "Bat_Pat.mp3", "Different"),
        ("Audio 2", "Ship_Sheep.mp3", "Different"),
        ("Audio 3", "Cat_Cat.mp3", "Same"),
        ("Audio 4", "Light_Right.mp3", "Different"),
        ("Audio 5", "Thin_Tin.mp3", "Different"),
    ]

    if 'phoneme_user_answers' not in st.session_state:
        st.session_state.phoneme_user_answers = ['Select an answer'] * len(phoneme_questions)

    for idx, (audio_label, audio_file, correct_answer) in enumerate(phoneme_questions):
        st.markdown(f"<h5>{audio_label}</h5>", unsafe_allow_html=True)

        # Play audio button
        audio_col, response_col = st.columns([1, 3])
        with audio_col:
            if st.button(f"Play {audio_label}", key=f"phoneme_play_{idx}"):
                # Update to use the correct audio path 
                audio_path =os.path.join('/Users/apple/Downloads/Audios_memory', audio_file)
                if os.path.exists(audio_path):
                    st.audio(audio_path, format='audio/mp3')  # Updated to .mp3 format
                else:
                    st.error(f"Audio file {audio_file} not found.")

        with response_col:
            # User response
            options = ['Select an answer', 'Same', 'Different']
            user_answer = st.radio(
                f"Do these audio clips sound the same or different? ({audio_label})",
                options=options,
                index=options.index(st.session_state.phoneme_user_answers[idx]) if st.session_state.phoneme_user_answers[idx] in options else 0,
                key=f"phoneme_{idx}"
            )
            st.session_state.phoneme_user_answers[idx] = user_answer

    st.markdown("---")  # Add a horizontal line separator


    # Rhyming Words Section
    st.subheader("📝 Rhyming Words")
    st.write("Listen to the word 'Bake' and select all the words that rhyme with it.")

    # Play the audio for 'Bake'
    if st.button("Play Audio for 'Bake'", key="rhyming_play_bake"):
        bake_audio_path = os.path.join('/Users/apple/Downloads/Audios_memory', audio_file)
        if os.path.exists(bake_audio_path):
            st.audio(bake_audio_path, format='audio/mp3')  # Updated to .mp3 format
        else:
            st.error("Audio file for 'Bake' not found.")

    # Options for rhyming words
    rhyming_options = ["Take", "Back", "Lake", "Bike"]
    rhyming_correct_answers = ["Take", "Lake"]

    # Add audio play buttons for each option
    for option in rhyming_options:
        if st.button(f"Play Audio for '{option}'", key=f"rhyming_play_{option.lower()}"):
            option_audio_path = os.path.join('/Users/apple/Downloads/Audios_memory', audio_file)
            if os.path.exists(option_audio_path):
                st.audio(option_audio_path, format='audio/mp3')  # Updated to .mp3 format
            else:
                st.error(f"Audio file for '{option}' not found.")

    # User selects the words
    if 'rhyming_user_answers' not in st.session_state:
        st.session_state.rhyming_user_answers = []

    rhyming_user_answers = st.multiselect(
        "Select words that rhyme with 'Bake':",
        rhyming_options,
        default=st.session_state.rhyming_user_answers,
        key="rhyming_words"
    )
    st.session_state.rhyming_user_answers = rhyming_user_answers

    st.markdown("---")  # Add a horizontal line separator



    # Sentence Repetition Section
    st.subheader("🗣️ Sentence Repetition")
    st.write("Listen to the following sentence and write it down.")

    # Play the audio for the sentence
    if st.button("Play Sentence Audio", key="sentence_play"):
        sentence_audio_path = os.path.join('/Users/apple/Downloads/Audios_memory', audio_file)
        if os.path.exists(sentence_audio_path):
            st.audio(sentence_audio_path, format='audio/mp3')  # Updated to .mp3 format
        else:
            st.error("Sentence audio file not found.")

    # Correct sentence answer
    sentence_correct_answer = "The quick brown fox jumps over the lazy dog."

    # Initialize session state for user's answer
    if 'sentence_user_answer' not in st.session_state:
        st.session_state.sentence_user_answer = ''

    # Input field for user's sentence
    sentence_user_answer = st.text_input(
        "Write down the sentence you heard:",
        value=st.session_state.sentence_user_answer,
        key="sentence_repetition"
    )
    st.session_state.sentence_user_answer = sentence_user_answer

    # Button to submit Audio Discrimination Test
    if st.button("Submit Audio Discrimination Test"):
        # Phoneme Discrimination Scoring
        phoneme_score = 0
        for idx, (user_answer, (question_text, audio_file, correct_answer)) in enumerate(zip(st.session_state.phoneme_user_answers, phoneme_questions)):
            if user_answer != 'Select an answer' and user_answer == correct_answer:
                phoneme_score += 0.1  # Each correct answer is worth 0.1
            # Else, score is 0 for this question

        # Rhyming Words Scoring
        rhyming_score = 0
        if st.session_state.rhyming_user_answers:
            correct_set = set(rhyming_correct_answers)
            user_set = set(st.session_state.rhyming_user_answers)
            rhyming_score = (len(correct_set & user_set) / len(correct_set)) * 0.1  # Proportional score

        # Stress Pattern Identification Scoring
        stress_score = 0

        # Initialize session state for 'stress_user_answer' if not already initialized
        if 'stress_user_answer' not in st.session_state:
             st.session_state.stress_user_answer = 'Select an answer'

# Then the rest of the code where you use `st.session_state.stress_user_answer`
        if st.session_state.stress_user_answer != 'Select an answer' and st.session_state.stress_user_answer == stress_correct_answer:
            stress_score = 0.1

        # Sentence Repetition Scoring
        sentence_score = 0
        if st.session_state.sentence_user_answer.strip() != '':
            if st.session_state.sentence_user_answer.strip().lower() == sentence_correct_answer.strip().lower():
                sentence_score = 0.3

        # Total Audio Discrimination Score
        total_audio_score = phoneme_score + rhyming_score + stress_score + sentence_score

        st.success(f"Phoneme Discrimination Score: {phoneme_score:.2f} / 0.5")
        st.success(f"Rhyming Words Score: {rhyming_score:.2f} / 0.1")
        st.success(f"Stress Pattern Identification Score: {stress_score:.2f} / 0.1")
        st.success(f"Sentence Repetition Score: {sentence_score:.2f} / 0.3")
        st.success(f"Total Audio Discrimination Score: {total_audio_score:.2f} / 1.0")

        # Store the total audio score in session state
        st.session_state.Audio_Discrimination = total_audio_score
else:
    st.warning("Time is up! Audio Discrimination Test is no longer available.")

st.markdown("---")  # Add a horizontal line separator

# Survey Test Section
st.header("📝 Survey Test")
st.write("Answer the following questions by selecting the most appropriate option:")

if not st.session_state.time_up:
    # Define the survey questions
    survey_questions = [
        "Do you often find it difficult to read words or letters in the correct order?",
        "Do you have trouble spelling common words correctly?",
        "Do you frequently mix up similar-looking letters like 'b' and 'd'?",
        "Do you find it hard to concentrate when reading or writing?",
        "Do you have difficulty remembering sequences such as phone numbers?"
    ]

    # Define the options and corresponding scores
    survey_options = ["Select an answer", "Yes", "Often", "Sometimes", "Not Often", "No"]
    survey_scores = {"Yes": 4, "Often": 3, "Sometimes": 2, "Not Often": 1, "No": 0}

    # Initialize user responses
    if 'survey_user_responses' not in st.session_state:
        st.session_state.survey_user_responses = ['Select an answer'] * len(survey_questions)

    # Loop through the questions and collect responses
    for i, question in enumerate(survey_questions):
        st.markdown(f"<h5>Question {i + 1}: {question}</h5>", unsafe_allow_html=True)
        response = st.radio(
            f"Select your answer for Question {i + 1}",
            survey_options,
            index=survey_options.index(st.session_state.survey_user_responses[i]) if st.session_state.survey_user_responses[i] in survey_options else 0,
            key=f"survey_q{i+1}"
        )
        st.session_state.survey_user_responses[i] = response

    # Submit button for survey test
    if st.button("Submit Survey Test"):
        # Calculate the raw score and scaled score
        raw_score = 0
        for resp in st.session_state.survey_user_responses:
            if resp != "Select an answer":
                raw_score += survey_scores[resp]
            # Else, score is 0 for this question
        scaled_score = raw_score / 20  # Total possible points = 20 (5 questions * 4 points max per question)

        # Display the results
        st.success(f"Survey Test Raw Score: {raw_score} / 20")
        st.success(f"Survey Test Scaled Score: {scaled_score:.2f} (0 = lowest, 1 = highest)")
        st.session_state.Survey_Score = scaled_score  # Store the score in session state
else:
    st.warning("Time is up! Survey Test is no longer available.")

st.markdown("---")  # Add a horizontal line separator

# Prediction Section
st.header("🔮 Dyslexia Prediction")
st.write("Based on your test scores and time taken, we will predict the likelihood of dyslexia.")

# Collect the scores from session state, default to 0 if not set
lang_vocab = st.session_state.get('Language_vocab', 0)
memory = st.session_state.get('Memory', 0)
visual = st.session_state.get('Visual_discrimination', 0)
audio = st.session_state.get('Audio_Discrimination', 0)
survey = st.session_state.get('Survey_Score', 0)

# Calculate the time taken in minutes
time_taken = (int(time.time()) - st.session_state.start_time) / 60  # Time in minutes

# Calculate the speed score
speed = max(0, min(1, 1 - (time_taken - min_time) / (max_time - min_time)))

# Display the time taken, time remaining, and speed score
time_remaining = max(0, max_time - time_taken)
st.info(f"**Time taken so far:** {time_taken:.2f} minutes")
st.info(f"**Time remaining until {max_time} minutes:** {time_remaining:.2f} minutes")
st.info(f"**Calculated Speed Score:** {speed:.2f} (1 = fastest at {min_time} minutes, 0 = slowest at {max_time} minutes)")

# Add a warning if any scores are zero
if any(score == 0 for score in [lang_vocab, memory, visual, audio, survey]):
    st.warning("Some test scores are zero due to unanswered questions. This may affect the accuracy of the prediction.")

# Function to make predictions
def predict_dyslexia(lang_vocab, memory, speed, visual, audio, survey):
    # Create a DataFrame for the new input data
    input_data = pd.DataFrame([[lang_vocab, memory, speed, visual, audio, survey]], columns=columns)
    # Scale the input data
    scaled_data = scaler.transform(input_data)
    # Predict using the model
    prediction = model.predict(scaled_data)
    # Interpret the result
    label = int(prediction[0])
    if label == 0:
        return "🚩 There is a **high chance** of the applicant having dyslexia."
    elif label == 1:
        return "⚠️ There is a **moderate chance** of the applicant having dyslexia."
    else:
        return "✅ There is a **low chance** of the applicant having dyslexia."

if st.button("Predict"):
    result = predict_dyslexia(lang_vocab, memory, speed, visual, audio, survey)
    if "high chance" in result:
        st.error(result)
    elif "moderate chance" in result:
        st.warning(result)
    else:
        st.success(result)