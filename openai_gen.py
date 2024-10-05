import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime, timedelta
import os
import pandas as pd
import re
import csv

# Initialize OpenAI client with the environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get yesterday's date in 'dd-mm-yyyy' format
yesterday = (datetime.now() - timedelta(1)).strftime('%d-%m-%Y')

# Base URL with yesterday's date
url = f'https://www.drishtiias.com/current-affairs-news-analysis-editorials/news-analysis/{yesterday}'

# Fetch the webpage content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the content inside the 'list-category' div
    list_category = soup.find('div', {'class': 'list-category'})

    if list_category:
        # Locate the <article> tag inside the 'list-category' div
        article_content = list_category.find('article')

        if article_content:
            # Fetch the text from the article
            text = article_content.get_text(strip=True)

            # Get today's date
            today_date = datetime.now().strftime("%Y-%m-%d")

            # Define the prompt to generate UPSC-level quiz questions
            prompt = f"""
            Generate 10 quiz questions based on the following text extracted from significant news topics.

            Ensure that the questions are relevant to the SSC exams and framed to encourage critical thinking.

            All questions must be based on the text provided below:

            Text: {text}

            The questions should cover a range of topics, including politics, economy, environment, and social issues.

            Also the options must be logical with the questions.

            Output must be a csv with headers: "question, A, B, C, D, answer".
            """

            # Call OpenAI API to generate quiz questions
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
            )

            # Extract the generated text from the response
            generated_text = response.choices[0].message.content

            # Debug: Print the generated text
            print("Generated Text:\n", generated_text)

            # Parse the generated text into a list of questions and answers
            questions = []
            lines = generated_text.strip().split('\n')

            for line in lines:
                # Remove double quotes and extra spaces from each line
                line = re.sub(r'"', '', line).strip()

                # Assuming each line contains a question followed by options and the answer
                parts = [part.strip() for part in line.split(',')]
                if len(parts) == 6:  # Ensure there are 5 options and an answer
                    questions.append(parts)

            # Create a DataFrame and remove any unwanted header-like rows
            df = pd.DataFrame(questions, columns=["question", "A", "B", "C", "D", "answer"])

            # Check and remove duplicate header row if present
            if df.iloc[0]['question'] == 'question':
                df = df.drop(index=0)

            # Save 6 questions for time constrains
            df_6 = df.head(6)

            # Define the CSV file name
            csv_file_name = f'data/quiz_questions_{today_date}.csv'

            # Save DataFrame to CSV without quotes and without the index
            df_6.to_csv(csv_file_name, index=False, quoting=csv.QUOTE_NONE, escapechar='\\')

            print(f'Successfully saved quiz questions to {csv_file_name}')
