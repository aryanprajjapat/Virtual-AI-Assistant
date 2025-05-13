import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
import logging

# Set up logging to log any errors or important information
logging.basicConfig(level=logging.INFO)

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}


async def open_images(prompt: str):
    folder_path = "Data"
    prompt = prompt.replace(" ", "_")
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            img = Image.open(image_path)
            logging.info(f"Opening image: {image_path}")
            img.show()
            await asyncio.sleep(1)
        except IOError:
            logging.error(f"Unable to open {image_path}")


async def query(payload):
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during request: {e}")
        return None


async def generate_images(prompt: str):
    tasks = []

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed = {randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    os.makedirs("Data", exist_ok=True)  # Ensure the folder exists

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            file_path = os.path.join("Data", f"{prompt.replace(' ', '_')}{i + 1}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)


async def generate_and_display_images(prompt: str):
    await generate_images(prompt)
    await open_images(prompt)


async def read_image_generation_data():
    try:
        with open(os.path.join("Frontend", "Files", "ImageGeneration.data"), "r") as f:
            data = f.read()
        prompt, status = data.split(",")
        return prompt, status
    except Exception as e:
        logging.error(f"Error reading image generation data: {e}")
        return None, None


async def main():
    while True:
        try:
            prompt, status = await read_image_generation_data()

            if prompt is None or status is None:
                await asyncio.sleep(1)
                continue

            if status.strip() == "True":
                logging.info("Generating Images...")
                await generate_and_display_images(prompt=prompt)

                with open(os.path.join("Frontend", "Files", "ImageGeneration.data"), "w") as f:
                    f.write("False,False")
                break
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")


# Run the main async function
if __name__ == "__main__":
    asyncio.run(main())
