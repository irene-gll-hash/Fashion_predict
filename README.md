# Fashion Trend AI

Проект для сбора fashion-контента, детекции объектов на изображениях, вырезания найденных предметов и получения fashion-атрибутов через Gemini.

## Пайплайн

```text
Apify / Instagram
→ изображения и кадры из видео
→ GroundingDINO detection
→ crop extraction
→ Gemini fashion attributes
→ fashion_attributes.json
```

## Структура

```text
fashion-trend-ai/
├── app/
│   ├── ai/
│   ├── apify/
│   ├── media/
│   ├── pipeline/
│   ├── storage/
│   └── taxonomy/
├── data/
│   └── raw/
│       ├── source_urls.txt
│       └── fashion_taxonomy.json
├── external/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
└── README.md
```

## Что хранится в Git

Добавляем в Git:

```text
app/
data/raw/source_urls.txt
data/raw/fashion_taxonomy.json
pyproject.toml
uv.lock
.python-version
.env.example
README.md
```

Не добавляем в Git:

```text
.env
.venv/
external/
data/processed/
media files
model weights
```

## Установка

Перейти в папку проекта:

```powershell
cd "C:\Users\Ирина Сулла\IdeaProjects\Fashion_predict\fashion-trend-ai"
```

Установить зависимости по lock-файлу:

```powershell
uv sync
```

Если проект ещё не инициализирован через uv:

```powershell
uv init --bare
uv python pin 3.11
uv add python-dotenv google-genai apify-client gigachat pillow numpy requests
uv add torch torchvision torchaudio
uv add transformers==4.30.2 timm addict yapf supervision
uv lock
```

## `.env`

Создать `.env` из примера:

```powershell
copy .env.example .env
```

Заполнить:

```env
APIFY_API_TOKEN=your_apify_api_token_here
GOOGLE_CLOUD_PROJECT=fashion-trend-ai
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
GIGACHAT_CREDENTIALS=your_gigachat_credentials_here
GIGACHAT_SCOPE=GIGACHAT_API_B2B
GIGACHAT_VERIFY_SSL=false
```

## Google Cloud / Gemini

Gemini используется через Google Cloud Vertex AI.

```powershell
gcloud auth login
gcloud config set project fashion-trend-ai
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
gcloud auth application-default set-quota-project fashion-trend-ai
```

В коде используется:

```python
genai.Client(
    vertexai=True,
    project=project,
    location=location,
)
```

## GroundingDINO

GroundingDINO лежит в:

```text
external/GroundingDINO/
```

Установка:

```powershell
uv pip install --no-build-isolation -e .\external\GroundingDINO
```

Веса должны лежать здесь:

```text
external/GroundingDINO/weights/groundingdino_swint_ogc.pth
```

## Входные файлы

Instagram-источники:

```text
data/raw/source_urls.txt
```

Fashion-категории для GroundingDINO:

```text
data/raw/fashion_taxonomy.json
```

В `fashion_taxonomy.json` хранится список категорий, которые GroundingDINO использует для text prompt.

## Запуск этапов

### 1. Apify

```powershell
uv run python -m app.pipeline.run_apify --limit 3
```

Результаты:

```text
data/processed/runs/<date>/raw_apify_posts.json
data/processed/runs/<date>/normalized_posts.json
data/processed/runs/<date>/media/images/
data/processed/runs/<date>/media/frames/
```

### 2. Detection

```powershell
uv run python -m app.pipeline.run_detection --run-date 2026-06-19
```

Тест:

```powershell
uv run python -m app.pipeline.run_detection --run-date 2026-06-19 --limit 50
```

Результат:

```text
data/processed/runs/<date>/detections.json
```

### 3. Crop extraction

Файл называется `run_segmentation.py`, но текущая версия не использует SAM-маски. Он вырезает RGB crop-ы по DINO box-ам.

```powershell
uv run python -m app.pipeline.run_segmentation --run-date 2026-06-19
```

Тест:

```powershell
uv run python -m app.pipeline.run_segmentation --run-date 2026-06-19 --limit 20
```

Результаты:

```text
data/processed/runs/<date>/segmentation/crops/
data/processed/runs/<date>/segmentation/segmentations.json
```

### 4. Gemini

```powershell
uv run python -m app.pipeline.run_gemini --run-date 2026-06-19
```

Тест:

```powershell
uv run python -m app.pipeline.run_gemini --run-date 2026-06-19 --limit 5
```

Переобработать уже готовые crop-ы:

```powershell
uv run python -m app.pipeline.run_gemini --run-date 2026-06-19 --force
```

Результат:

```text
data/processed/runs/<date>/fashion_attributes.json
```

## Запуск через `run_all.py`

Все этапы по умолчанию:

```powershell
uv run python -m app.pipeline.run_all
```

Выбранные этапы:

```powershell
uv run python -m app.pipeline.run_all --steps detection,segmentation,gemini --run-date 2026-06-19
```

Тестовый прогон:

```powershell
uv run python -m app.pipeline.run_all --steps detection,segmentation,gemini --run-date 2026-06-19 --detection-limit 20 --segmentation-limit 20 --gemini-limit 5
```

Показать команды без запуска:

```powershell
uv run python -m app.pipeline.run_all --steps detection,segmentation,gemini --run-date 2026-06-19 --dry-run
```

Переобработать Gemini через `run_all.py`:

```powershell
uv run python -m app.pipeline.run_all --steps gemini --run-date 2026-06-19 --force-gemini
```

## Параметры

### `run_detection.py`

```text
--run-date
--limit
--box-threshold
--text-threshold
--nms-iou-threshold
```

Рекомендуемые значения:

```text
box-threshold = 0.35
text-threshold = 0.25
nms-iou-threshold = 0.5
```

### `run_segmentation.py`

```text
--run-date
--limit
```

Внутренние константы:

```python
CROP_PADDING = 0.12
MIN_CROP_SIZE = 96
```

### `run_gemini.py`

```text
--run-date
--limit
--force
```

По умолчанию уже успешно обработанные crop-ы пропускаются.

### `run_all.py`

```text
--steps
--run-date
--apify-limit
--detection-limit
--segmentation-limit
--gemini-limit
--dry-run
--force-gemini
```

## Проверка результата

После запуска должны появиться:

```text
data/processed/runs/<date>/detections.json
data/processed/runs/<date>/segmentation/segmentations.json
data/processed/runs/<date>/fashion_attributes.json
```

Итоговый файл для анализа:

```text
data/processed/runs/<date>/fashion_attributes.json
```

## Git

Добавить основные файлы:

```powershell
git add fashion-trend-ai/app
git add fashion-trend-ai/data/raw/source_urls.txt
git add fashion-trend-ai/data/raw/fashion_taxonomy.json
git add fashion-trend-ai/pyproject.toml
git add fashion-trend-ai/uv.lock
git add fashion-trend-ai/.python-version
git add fashion-trend-ai/.env.example
git add fashion-trend-ai/README.md
git commit -m "Prepare fashion trend pipeline"
```

Проверить статус:

```powershell
git status
```
