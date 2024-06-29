from typing import Union, Annotated, List

from fastapi import FastAPI, Form, UploadFile, File

import settings
from api_types import GenerationItem, GenerateResponseItem
from luma import Sdk

app = FastAPI()
sdk = Sdk(username='test', password='test', profile_root='./storage/profile/0')


sdk.add_access_token(settings.access_token)


@app.post("/api/v1/generate")
def generate(user_prompt: Annotated[str, Form()], image: Annotated[UploadFile, File()] = None, expand_prompt: Annotated[bool, Form()] = False) -> str:
    print(image)
    image_path = None
    if image:
        image_path = f'/tmp/{image.filename}'
        with open(image_path, 'wb') as f:
            f.write(image.file.read())
    return sdk.generate(user_prompt, image_path, expand_prompt)


@app.get('/api/v1/generations')
def get_generations() -> List[GenerationItem]:
    return sdk.get_generations()
