from flask import Flask, request, render_template ,jsonify
from PIL import Image  
from flask_cors import CORS
import torch  
import torchvision
import torchvision.transforms as transforms
import io
import base64 


CLASS_NAME = ['Aluminium', 'Carton', 'E-waste', 'Glass', 'Organic_Waste', 'Paper_and_Cardboard', 'Plastics', 'Textiles', 'Wood']

app = Flask(__name__)
CORS(app) 

@app.route('/')
def home():
    return render_template('home.html')

def build_model():
    weights = torchvision.models.resnet50(pretrained=True)
    model = torchvision.models.resnet50(weights=weights).to('cpu')

    model.fc = torch.nn.Linear(in_features=2048,
                        out_features=len(CLASS_NAME),
                        bias=True).to('cpu')
                        
    model.load_state_dict(torch.load("models/MultiClassResNET50Model4.pth", map_location='cpu'))

    return model

model = build_model()

def process_image(image):
    # Convert RGBA to RGB if necessary
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    transformation = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.CenterCrop(224),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.299, 0.224, 0.225])
    ])

    image_tensor = transformation(image).unsqueeze(0)

    return image_tensor


@app.route('/predict', methods=['POST'])
def predict():
    # Get uploaded image file
    image = request.files['image']

    model.eval()
    # Process image and make prediction
    image_tensor = process_image(Image.open(image))
    output = model(image_tensor)

    # Get class probabilities
    probabilities = torch.nn.functional.softmax(output, dim=1)
    probabilities = probabilities.detach().numpy()[0]

    # Get the index of the highest probability
    class_index = probabilities.argmax()

    # Get the predicted class and probability
    predicted_class = CLASS_NAME[class_index]
    probability = probabilities[class_index]

    # Sort class probabilities in descending order
    class_probs = list(zip(CLASS_NAME, probabilities))
    class_probs.sort(key=lambda x: x[1], reverse=True)

    # Return JSON response
    return jsonify({
        'predicted_class': predicted_class,
        'probability': float(probability),
        'class_probs': [(class_name, float(prob)) for class_name, prob in class_probs]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
