# SlidesAI

An AI-powered presentation generation system that automatically creates professional presentations with custom diagrams and themes.

## 🌟 Features

- 🤖 AI-powered content generation
- 📊 Custom diagram creation
- 🎨 Multiple professional themes
- 🔄 Real-time preview
- 📱 Responsive interface
- 🔗 Google Slides integration

## 📁 Project Structure

```
slidesai/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py
│   │
│   ├── services/
│   │   ├── diagram_service.py
│   │   ├── google_service.py
│   │   ├── openai_service.py
│   │   └── presentation_service.py
│   │
│   ├── models/
│   │   └── sd-ai2d-model/        # Trained diagram model
│   │
│   └── utils/
│       ├── content_validator.py   # Content validation
│       └── text_processor.py      # Text processing
│
├── frontend/
│   ├── streamlit_app.py          # Streamlit application
│   ├── config.py
│   │
│   └── utils/
│       ├── theme_previews.py     # Theme previews
│       └── ui_helpers.py         # UI utilities
│
├── training/
│   └── slidesai-diagram-generator.ipynb  # Training notebook
│
├── .env.example                  # Environment template
└── requirements.txt              # Project dependencies
```

## 🚀 Quick Start

1. **Clone Repository**

   ```bash
   git clone https://github.com/saketsarin/slidesai.git
   cd slidesai
   ```

2. **Set Up Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/macOS
   # or
   .\venv\Scripts\activate  # Windows

   pip install -r requirements.txt
   ```

3. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start Backend**

   ```bash
   cd backend
   python app.py
   ```

5. **Launch Frontend**
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```

## 🛠️ Prerequisites

- Python 3.8+
- CUDA-capable GPU (8GB+ VRAM recommended)
- Google Cloud Platform account
- OpenAI API key
