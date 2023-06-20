import asyncio
import openai
import os
import re
from aiohttp import ClientSession
from datetime import datetime
import stable_diffusion_generation
import time
from prompts import *
import subprocess




# Set up the API client
openai.api_key = "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"
openai.organization = "org-rLLsbN71s2gi6Qp3oPUHXieH"




def read_sources(file_path):
    with open(file_path, 'r') as file:
        urls = file.readlines()
    return [url.strip() for url in urls]

def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


async def fetch(prompt, session, semaphore):
    async with semaphore:
        max_retries = 6
        for attempt in range(max_retries):
            try:
                scrape_messages = []
                scrape_messages.append({"role": "system", "content": scraper_system_prompt})
                scrape_messages.append({"role": "assistant", "content": prompt})

                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=scrape_messages,
                    temperature=0.3
                )

            except Exception as e:
                print(f"Error fetching response for prompt on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:  # not the last attempt
                    print("Retrying...")
                    await asyncio.sleep(2)  # wait for 2 seconds before next attempt
                    continue
                else:  # last attempt
                    print("All attempts failed.")
                    return ""

            if "choices" not in response:
                print(f"Response format error for prompt")
                return ""

        print(response["choices"][0]["message"]["content"])
        return response["choices"][0]["message"]["content"]



async def fetch_all(prompts):
    tasks = []
    semaphore = asyncio.Semaphore(10)
    async with ClientSession() as session:
        for prompt in prompts:
            task = asyncio.ensure_future(fetch(prompt, session, semaphore))
            tasks.append(task)

        completed = 0
        total = len(prompts)
        print(f"Begun {total} requests")

        responses = []  # create an empty responses list before the loop

        while tasks:
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            completed += len(done)
            print(f"Completed {completed}/{total} requests")

            for completed_task in done:
                response = await completed_task  # Await the result of the completed task
                responses.append(response)


    return responses





def write_article(article):


    print("Begun Generating Article.")

    article_messages = []

    article_messages.append({"role": "system", "content": writer_system_prompt})

    for response in article:
        message = {"role": "assistant", "content": response}
        article_messages.append(message)


   
    article_messages.append({"role": "assistant", "content": write_article_prompt})


    max_retries = 6
    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=article_messages,
                temperature=0.2
            )["choices"][0]["message"]["content"].replace("##", "#").replace("##", "#")
            break  # if successful, break the retry loop
        except Exception as e:
            print(f"Error fetching response on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:  # not the last attempt
                print("Retrying...")
                time.sleep(2)  # wait for 2 seconds before next attempt
            else:  # last attempt
                print("All attempts failed.")
                return

    print("Article Generation Complete.")

    print("Generating Citations")

    citations = []
    folder_path = "topicinformation"
    sources_file = f"{folder_path}/sources.txt"

    # Read the source URLs
    sources = read_sources(sources_file)

    # Format each URL and append it to citation_messages
    for source in sources:
        formatted_source = f"[{source}]({source})"
        citations.append(formatted_source)
        citations.append('\n\n')

    citation_response = "".join(citations)

    full_response = response + "\n\n## Sources:\n\n" + citation_response

    # Extract the article title from the generated text
    title_match = re.search(r"title:\s+(.+)\n", full_response)
    article_title = title_match.group(1) if title_match else ""
    image_prompt = article_title
    article_title = article_title.replace(" ", "-").lower()

    # Create a directory with the article title and save the generated article to a markdown file
    output_dir_path = os.path.join("generated-content", re.sub(r"[^a-zA-Z0-9]+", "-", article_title).lower())
    os.makedirs(output_dir_path, exist_ok=True)
    output_file_path = os.path.join(output_dir_path, "index.mdx")
    with open(output_file_path, "w", encoding="utf-8") as f:
        generated_text = full_response
        f.write(generated_text.replace('\u2009', ' '))

    print("Article Finished and Saved.")



    ## Generates Image. Turn this off when potentially offensive pictures could be generated
    print("Generating Cover Image Description.")

    cover_messages = []

    cover_messages.append({"role": "system", "content": image_cover_system_prompt})
    cover_request = "Describe a cover image for " + image_prompt
    

    cover_messages.append({"role": "assistant", "content": cover_request})

    max_retries = 6
    for attempt in range(max_retries):
        try:
            cover_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=cover_messages,
                temperature = 1
            )["choices"][0]["message"]["content"]
            break  # if successful, break the retry loop
        except Exception as e:
            print(f"Error fetching cover response on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:  # not the last attempt
                print("Retrying...")
                time.sleep(2)  # wait for 2 seconds before next attempt
            else:  # last attempt
                cover_response = ""  # or any other default value

    
    stable_diffusion_generation.generate_image_from_text(cover_response + image_style_prompt, output_dir_path, 1)



    print("Generating Cover Image Complete")   

    subprocess.run(["node", "sanityupload.js", output_dir_path], check=True)






# Generate the article in raw markdown format
async def generate_article():
    
    

    

    # Read the text file
    file_path = "topicinformation/gatheredinformation.txt"
    with open(file_path, "r", encoding="utf-8") as f:
        text_data = f.read()

    # Split the text data into smaller chunks (if needed) to avoid exceeding the token limit
    chunk_size = 8000  # increased chunk size
    text_chunks = [text_data[i:i + chunk_size] for i in range(0, len(text_data), chunk_size)]
    #text_chunks = re.split('<\?!>', text_data)[1:]

    prompts = [f"{scraper_prompt} {chunk}" for chunk in text_chunks]

    # Fetch responses from OpenAI's API
    responses = await fetch_all(prompts)

    article = [] 

    # Combine responses into a single article
    for response in responses:
        if response:
            article.append(response)

    # assuming write_article is defined somewhere and it's an async function
    write_article(article)


if __name__ == "__main__":
    asyncio.run(generate_article()) 