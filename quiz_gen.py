import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import pandas as pd
import re
import csv
import google.generativeai as genai

# Configure the Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Get yesterday's date in 'dd-mm-yyyy' format
yesterday = (datetime.now() - timedelta(1)).strftime('%d-%m-%Y')

# DD News RSS feed URL
dd_news_url = "https://ddnews.gov.in/en/feed"

# Wikipedia current events portal URL
wiki_url = "https://en.wikipedia.org/wiki/Portal:Current_events"

# Function to fetch content from DD News
def fetch_dd_news_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching DD News URL: {e}")
        return None

    # Use 'lxml-xml' parser for XML
    soup = BeautifulSoup(response.content, 'lxml-xml')  
    items = soup.find_all('item')
    
    news_items = []
    for item in items:
        title = item.title.text
        description = item.description.text
        news_items.append(f"{title} {description}")  # Combine title and description

    if news_items:
        return news_items  # Return all news items
    print("No news items found in DD News feed.")
    return None

# Function to fetch content from Wikipedia
def fetch_wiki_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching Wikipedia URL: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    current_events_section = soup.find('div', class_='p-current-events-events')

    if current_events_section:
        return current_events_section.get_text(strip=True)
    print("Could not find the current events section on Wikipedia.")
    return None

# Fetch DD News content
dd_news_texts = fetch_dd_news_content(dd_news_url)

# If DD News content is not found, fetch from Wikipedia
if not dd_news_texts:
    print("Using Wikipedia as fallback...")
    wiki_text = fetch_wiki_content(wiki_url)

    if wiki_text:
        print("Wikipedia content retrieved successfully.")
        text_to_use = wiki_text
    else:
        print("No valid content found in either DD News or Wikipedia.")
        exit(1)
else:
    print("DD News content retrieved successfully.")
    text_to_use = "\n".join(dd_news_texts)  # Combine all news items into a single text

# Only proceed if valid content is found
if text_to_use.strip():
    # Set up the quiz generation request for the Gemini API
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 1024,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=f"""
                    You are an expert quiz creator specializing in generating questions for SSC exams. Your task is to create 10 concise multiple-choice questions based on the provided text, which contains information on significant news topics.

                    Input: {text_to_use}

                    Instructions:
                    1. Generate 10 quiz questions that are directly based on the given text.
                    2. Ensure questions are relevant to SSC exams and encourage critical thinking.
                    3. Cover a range of topics including politics, economy, environment, and social issues.
                    4. Keep questions brief and to the point.
                    5. Provide four answer options (A, B, C, D) for each question. Each option must be very concise - ideally 1-5 words, and no more than 6 words.
                    6. Indicate the correct answer for each question.

                    Output Format:
                    Produce a CSV with the following headers: "question,A,B,C,D,answer"

                    Example output:
                    question,A,B,C,D,answer
                    "Brief question text?",Option A,Option B,Option C,Option D,B

                    Guidelines:
                    - Ensure all questions and answers are factually accurate and based solely on the provided text.
                    - Avoid overly complex language or jargon.
                    - Frame questions to test understanding and analysis rather than mere factual recall.
                    - Maintain a balance between difficulty levels across the 10 questions.
                    - Double-check that all correct answers are unambiguous based on the given text.
                    - Prioritize brevity in both questions and answer options without sacrificing clarity.
                    """
    )

    # Start a chat session with the model
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message("Generate the quiz questions")

    # Extract the generated text from the response
    generated_text = response.text
    print("Generated Text:\n", generated_text)

    # Parse the generated text into a list of questions and answers
    questions = []
    lines = generated_text.strip().split('\n')

    for line in lines[1:]:  # Skip the header
        # Remove double quotes and extra spaces from each line
        line = re.sub(r'"', '', line).strip()

        # Assuming each line contains a question followed by options and the answer
        parts = [part.strip() for part in line.split(',')]
        if len(parts) == 6:  # Ensure there are 5 options and an answer
            questions.append(parts)

    # Create a DataFrame
    df = pd.DataFrame(questions, columns=["question", "A", "B", "C", "D", "answer"])

    # Ensure we only keep valid questions
    df = df[df['question'] != 'question']  # Remove any rows where the question is a header

    # Save 6 questions for time constraints
    df_6 = df.head(6)

    # Get today's date for the filename
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Define the CSV file name
    csv_file_name = f'data/quiz_questions_{today_date}.csv'

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(csv_file_name), exist_ok=True)

    # Save DataFrame to CSV without quotes and without the index
    df_6.to_csv(csv_file_name, index=False, quoting=csv.QUOTE_MINIMAL, escapechar='\\')

    print(f'Successfully saved quiz questions to {csv_file_name}')
else:
    print("No valid text available for quiz generation.")
