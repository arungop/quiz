from openai import OpenAI
from datetime import datetime
import pandas as pd

client = OpenAI(api_key="OPEN_API_KEY")

# Get today's date
today_date = datetime.now().strftime("%Y-%m-%d")

# Define the prompt to generate UPSC-level quiz questions
prompt = f"""
Generate 10 quiz questions based on significant news in India from {today_date}.
Ensure that the questions are relevant, factually accurate, and tailored for UPSC exams.
Each question should have four options (A, B, C, D) and specify the correct answer.
Format each output line as: "Question, A, B, C, D, CorrectAnswer".
If you cannot provide factual information, state that instead of providing placeholders.
"""

# Call OpenAI API to generate quiz questions
response = client.chat.completions.create(
    model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
)

# Extract the generated text from the response
generated_text = response.choices[0].message.content

# Debug: Print the generated text
print("Generated Text:\n", generated_text)

# Process the generated text to structure it for CSV
lines = generated_text.strip().split("\n")
data = []

for line in lines:
    # Split the line by commas
    parts = line.split(",")

    # Check if we have the expected number of parts
    if len(parts) == 6:
        question, a, b, c, d, answer = [part.strip() for part in parts]
        data.append(
            {
                "Question": question,
                "A": a,
                "B": b,
                "C": c,
                "D": d,
                "Answer": answer,
            }
        )
    else:
        print(f"Skipping line due to unexpected format: {line}")

# Create a DataFrame and save it as CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv(f"data/upsc_quiz_questions_{today_date}.csv", index=False)
    print("CSV file 'upsc_quiz_questions.csv' has been created successfully.")
else:
    print("No valid quiz questions generated.")
