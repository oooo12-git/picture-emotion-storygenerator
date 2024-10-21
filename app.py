import os
from flask import Flask, request, render_template
from openai import OpenAI
from PIL import Image
import base64
import io

client = OpenAI()

app = Flask(__name__)

# 저장할 디렉토리 설정 (예: 'uploads/')
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 홈 페이지: 그림 업로드와 감정 선택을 받음
@app.route('/')
def index():
    return render_template('index.html')

# 파일 업로드 처리 및 이야기 생성
@app.route('/upload', methods=['POST'])
def upload_and_generate():
    # 업로드된 그림들 가져오기
    images = request.files.getlist("images")
    emotion = request.form.get("emotion")

    # 이미지를 서버에 저장
    saved_image_paths = []
    for image in images:
        # 파일을 특정 디렉토리에 저장
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)  # FileStorage 객체의 save() 메서드로 파일 저장
        saved_image_paths.append(image_path)

    # 저장된 이미지 파일들을 base64로 인코딩
    base64_images = [encode_image(image_path) for image_path in saved_image_paths]

    # 각 그림에 대한 설명 생성
    descriptions = []
    for base64_image in base64_images:
        #img = Image.open(image)
        # OpenAI API를 통해 그림 분석
        description = analyze_image(base64_image)
        descriptions.append(description)
    
    # 감정 기반 이야기 생성
    story = generate_story(descriptions, emotion)

    return render_template('story.html', story=story)

def encode_image(image_path):
    # 이미지 파일을 base64로 인코딩
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image):
    # OpenAI API로 이미지를 분석하여 설명 텍스트 생성
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "What is in this image?",
            },
            {
            "type": "image_url",
            "image_url": {
                "url":  f"data:image/jpeg;base64,{image}"
                },
            },
            ],
        }
        ],
    )
    return response.choices[0].message.content

def generate_story(descriptions, emotion):
    # 각 그림 설명을 기반으로 감정에 맞는 스토리 생성
    prompt = f"Create a {emotion} story based on the following images:\n"
    for desc in descriptions:
        prompt += f"{desc}\n"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": f"{prompt} 한글로 써줘",
            },
            ],
        },
        ]
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run()