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

# Base URL with yesterday's date
url = f'https://www.drishtiias.com/current-affairs-news-analysis-editorials/news-analysis/{yesterday}'

# Fetch the webpage content
try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
except requests.RequestException as e:
    print(f"Error fetching the URL: {e}")
else:
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the content inside the 'list-category' div
    list_category = soup.find('div', {'class': 'list-category'})

    if list_category:
        # Locate the <article> tag inside the 'list-category' div
        article_content = list_category.find('article')

        if article_content:
            # Fetch the text from the article
            text = article_content.get_text(strip=True)

            # Create the model
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            model = genai.ChatGoogleGenerativeAI(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                system_instruction=f"""
                Generate 10 quiz questions based on the following text extracted from significant news topics.

                Ensure that the questions are relevant to the SSC exams and framed to encourage critical thinking.

                All questions must be based on the text provided below:

                Text: {text}

                The questions should cover a range of topics, including politics, economy, environment, and social issues.

                Also the options must be logical with the questions.

                Answer must be from [A, B, C, D]

                Output must be a csv with headers: "question, A, B, C, D, answer".
                """
            )

            # Start a chat session with the model
            chat_session = model.start_chat(history=[])
            response = chat_session.send_message("Generate the quiz questions")

            # Extract the generated text from the response
            generated_text = response.text

            # Debug: Print the generated text
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
            print("No article content found in the list-category div.")
    else:
        print("No list-category div found in the page.")
