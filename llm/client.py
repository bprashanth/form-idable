import json
from openai import OpenAI
from pathlib import Path


class ModelClient:
    def __init__(self, api_key, model="gpt-5-mini"):
        # Vision-capable model, other options: gpt-5 and gpt-5-mini and
        # gpt-4.1-mini, gpt-4.1 - but note that there is a 3-5x
        # difference in cost between the mini and non-mini models
        self.model = model
        self.client = OpenAI(api_key=api_key)
        print(f"Using model: {self.model}")

    def infer(self, prompt, image_urls):
        """Run inference with given prompt and one or many images.

        If there are more than one image in this list, it is assumed that the prompt in question knowns how to phrase the questions accoutning for this. Eitherways, this method makes exactly one call to the API.

        @param prompt: Prompt object with .system() and .user() methods.
        @param image_urls: List of URLs. 

        @return: List of raw OpenAI API responses (one per image in non-batch 
            mode, one response for all images in batch mode - but still wrapped 
            in a list).
        """
        if not isinstance(image_urls, list):
            image_urls = [image_urls]

        content = [{"type": "text", "text": prompt.user()}]
        unique_file_names = set()
        for url in image_urls:
            # Extract filename from URL or path
            filename = Path(url).name
            if filename in unique_file_names:
                raise ValueError(
                    f"Duplicate filename found: {filename} in {image_urls}")
            unique_file_names.add(filename)
            # Add the text stub so the model can echo it back
            content.append(
                {"type": "text", "text": f"source_file: {filename}"})
            # Add the image itself
            content.append({"type": "image_url", "image_url": {"url": url}})

        params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.system()},
                {"role": "user", "content": content}
            ]
        }

        # temperature
        if "gpt-4" in self.model:
            params["temperature"] = 0.0

        response = self.client.chat.completions.create(**params)
        # Return the raw OpenAI API response directly
        return response
