# Fashion Trend AI

Fashion Trend AI — pipeline для автоматизированной обработки fashion-контента из Instagram: сбор постов, скачивание медиафайлов, распознавание fashion-объектов на изображениях и кадрах из видео, выделение найденных объектов в crop-изображения и дальнейший анализ fashion-атрибутов через Gemini.

Проект рассчитан на два режима работы:

```text
1. Локальный запуск — для разработки, тестирования и отладки отдельных этапов.
2. Облачный запуск — для воспроизводимого выполнения pipeline через Google Cloud Run GPU Job.
```

## Общая схема pipeline

```text
Instagram sources
→ Apify Instagram scraper
→ raw_apify_posts.json
→ normalized_posts.json
→ download images / video frames
→ GroundingDINO detection
→ detections.json
→ segmentation / crop extraction
→ segmentations.json + crops/
→ Gemini fashion attributes
→ fashion_attributes.json
```

## Основные возможности

```text
Сбор Instagram-контента через Apify.
Нормализация сырых Apify-данных в единый внутренний формат.
Скачивание изображений из постов.
Извлечение кадров из видео.
Распознавание fashion-объектов через GroundingDINO.
Сохранение координат найденных объектов и confidence score.
Выделение найденных объектов в отдельные crop-изображения.
Анализ crop-изображений через Gemini.
Сохранение результатов в локальную run-директорию.
Выгрузка результатов в Google Cloud Storage.
Сборка Docker image через Cloud Build.
Запуск pipeline в Cloud Run GPU Job с NVIDIA L4.
```

## Структура проекта

Репозиторий:

```text
Fashion_predict/
├── Dockerfile.gpu
├── cloudbuild.gpu.yaml
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── .dockerignore
├── README.md
└── fashion-trend-ai/
    ├── app/
    │   ├── ai/
    │   ├── apify/
    │   ├── gpu_service/
    │   ├── media/
    │   ├── pipeline/
    │   ├── storage/
    │   └── taxonomy/
    ├── data/
    │   ├── raw/
    │   │   ├── source_urls.txt
    │   │   ├── fashion_taxonomy.json
    │   │   └── mock_apify_posts.json
    │   └── processed/
    │       └── runs/
    ├── external/
    ├── .env.example
    └── requirements.txt
```

## Что хранится в Git

В Git добавляются:

```text
Dockerfile.gpu
cloudbuild.gpu.yaml
pyproject.toml
uv.lock
.python-version
README.md
fashion-trend-ai/app/
fashion-trend-ai/data/raw/source_urls.txt
fashion-trend-ai/data/raw/fashion_taxonomy.json
fashion-trend-ai/data/raw/mock_apify_posts.json
fashion-trend-ai/.env.example
```

В Git не добавляются:

```text
.env
.venv/
fashion-trend-ai/external/
fashion-trend-ai/data/processed/
media files
model weights
Google credentials
API tokens
```

## Основные входные файлы

### `source_urls.txt`

Файл со списком Instagram-источников:

```text
fashion-trend-ai/data/raw/source_urls.txt
```

Пример:

```text
https://www.instagram.com/zara/
https://www.instagram.com/mango/
https://www.instagram.com/hm/
```

### `fashion_taxonomy.json`

Файл с fashion-категориями для GroundingDINO prompt:

```text
fashion-trend-ai/data/raw/fashion_taxonomy.json
```

Используется на этапе detection для поиска нужных типов одежды, обуви, сумок, аксессуаров и других fashion-объектов.

### `mock_apify_posts.json`

Тестовый файл с примером сырого ответа Apify Instagram scraper:

```text
fashion-trend-ai/data/raw/mock_apify_posts.json
```

Используется для разработки и проверки нормализации без обязательного обращения к Apify API.

## Результаты pipeline

Каждый запуск сохраняется в отдельную папку по дате:

```text
fashion-trend-ai/data/processed/runs/<date>/
```

Пример:

```text
fashion-trend-ai/data/processed/runs/2026-06-29/
```

Структура результата:

```text
runs/<date>/
├── raw_apify_posts.json
├── normalized_posts.json
├── detections.json
├── media/
│   ├── images/
│   └── frames/
└── segmentation/
    ├── segmentations.json
    └── crops/
```

После этапа Gemini дополнительно появляется:

```text
runs/<date>/fashion_attributes.json
```

Если включена выгрузка в Google Cloud Storage, такая же структура сохраняется в bucket:

```text
gs://fashion-trend-ai-runs/runs/<date>/
```

## Переменные окружения

Для локального запуска используется файл:

```text
fashion-trend-ai/.env
```

Создать `.env` из примера:

```powershell
copy .\fashion-trend-ai\.env.example .\fashion-trend-ai\.env
```

Пример `.env`:

```env
APIFY_API_TOKEN=your_apify_token_here

GOOGLE_CLOUD_PROJECT=fashion-trend-ai
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

GIGACHAT_CREDENTIALS=your_gigachat_credentials_here
GIGACHAT_SCOPE=GIGACHAT_API_B2B
GIGACHAT_VERIFY_SSL=false

GCS_BUCKET=fashion-trend-ai-runs

REQUIRE_CUDA=0
```

Назначение переменных:

```text
APIFY_API_TOKEN — токен Apify для запуска Instagram scraper.
GOOGLE_CLOUD_PROJECT — Google Cloud project id.
GOOGLE_CLOUD_LOCATION — регион Vertex AI / Gemini.
GEMINI_MODEL — используемая Gemini-модель.
GIGACHAT_CREDENTIALS — credentials для GigaChat, если используется GigaChat-этап.
GIGACHAT_SCOPE — scope для GigaChat API.
GIGACHAT_VERIFY_SSL — проверка SSL для GigaChat.
GCS_BUCKET — bucket для выгрузки результатов.
REQUIRE_CUDA — требовать CUDA или разрешить CPU fallback.
```

Для локального запуска без NVIDIA GPU:

```env
REQUIRE_CUDA=0
```

Для облачного GPU-запуска:

```env
REQUIRE_CUDA=1
```

В Cloud Run эта переменная задаётся не через локальный `.env`, а через настройки job.

## Локальная установка

Перейти в корень репозитория:

```powershell
cd "C:\Users\Ирина Сулла\IdeaProjects\Fashion_predict"
```

Установить зависимости:

```powershell
uv sync
```

Проверить Python:

```powershell
uv run python --version
```

Проверить импорт основных модулей:

```powershell
uv run python -c "import torch; print(torch.__version__)"
```

## Локальная установка GroundingDINO

GroundingDINO не хранится в Git. Для локального запуска detection его нужно установить отдельно.

Создать папку `external`, если её нет:

```powershell
New-Item -ItemType Directory -Force .\fashion-trend-ai\external
```

Склонировать GroundingDINO:

```powershell
git clone https://github.com/IDEA-Research/GroundingDINO.git `
  .\fashion-trend-ai\external\GroundingDINO
```

Скачать веса:

```powershell
New-Item -ItemType Directory -Force `
  .\fashion-trend-ai\external\GroundingDINO\weights

curl.exe -L `
  -o .\fashion-trend-ai\external\GroundingDINO\weights\groundingdino_swint_ogc.pth `
  https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
```

Установить GroundingDINO локально:

```powershell
uv pip install --no-build-isolation -e .\fashion-trend-ai\external\GroundingDINO
```

Проверить наличие весов:

```powershell
Test-Path .\fashion-trend-ai\external\GroundingDINO\weights\groundingdino_swint_ogc.pth
```

## Локальная авторизация Google Cloud

Для локального запуска Gemini и выгрузки в GCS:

```powershell
gcloud auth login
gcloud config set project fashion-trend-ai
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
gcloud auth application-default set-quota-project fashion-trend-ai
```

Проверить активный проект:

```powershell
gcloud config get-value project
```

## Локальный запуск pipeline

Команды лучше выполнять из папки приложения:

```powershell
cd "C:\Users\Ирина Сулла\IdeaProjects\Fashion_predict\fashion-trend-ai"
```

### Полный локальный запуск

```powershell
uv run python -m app.pipeline.run_all
```

По умолчанию запускаются этапы:

```text
apify
detection
segmentation
gemini
```

### Тестовый локальный запуск

Для быстрой проверки лучше ограничивать количество данных:

```powershell
uv run python -m app.pipeline.run_all `
  --apify-limit 1 `
  --detection-limit 3 `
  --segmentation-limit 3 `
  --gemini-limit 3
```

### Запуск выбранных этапов

```powershell
uv run python -m app.pipeline.run_all `
  --steps detection,segmentation,gemini `
  --run-date 2026-06-29
```

### Dry run

Показать команды без запуска:

```powershell
uv run python -m app.pipeline.run_all `
  --steps detection,segmentation,gemini `
  --run-date 2026-06-29 `
  --dry-run
```

## Локальный запуск отдельных этапов

### 1. Apify

```powershell
uv run python -m app.pipeline.run_apify --limit 5
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
uv run python -m app.pipeline.run_detection --run-date 2026-06-29
```

Тест с ограничением:

```powershell
uv run python -m app.pipeline.run_detection `
  --run-date 2026-06-29 `
  --limit 20
```

Результат:

```text
data/processed/runs/<date>/detections.json
```

`detections.json` содержит:

```text
image_id
image_path
media_type
post_url
source_username
width
height
detections[]
```

Внутри каждого detection:

```text
label
score
box_xyxy
box_cxcywh_norm
```

### 3. Segmentation

```powershell
uv run python -m app.pipeline.run_segmentation --run-date 2026-06-29
```

Тест с ограничением:

```powershell
uv run python -m app.pipeline.run_segmentation `
  --run-date 2026-06-29 `
  --limit 20
```

Результаты:

```text
data/processed/runs/<date>/segmentation/segmentations.json
data/processed/runs/<date>/segmentation/crops/
```

Этап segmentation использует результаты detection, выделяет найденные fashion-объекты и сохраняет crop-изображения для дальнейшего анализа.

### 4. Gemini

```powershell
uv run python -m app.pipeline.run_gemini --run-date 2026-06-29
```

Тест с ограничением:

```powershell
uv run python -m app.pipeline.run_gemini `
  --run-date 2026-06-29 `
  --limit 5
```

Принудительная переобработка:

```powershell
uv run python -m app.pipeline.run_gemini `
  --run-date 2026-06-29 `
  --force
```

Результат:

```text
data/processed/runs/<date>/fashion_attributes.json
```

## Параметры pipeline

### `run_all.py`

```text
--steps
--run-date
--apify-limit
--detection-limit
--segmentation-limit
--gemini-limit
--box-threshold
--text-threshold
--nms-iou-threshold
--force-gemini
--dry-run
```

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

Внутренние параметры:

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

## Облачная архитектура

Облачный запуск использует Google Cloud:

```text
GitHub / local source code
→ Cloud Build
→ Artifact Registry Docker image
→ Cloud Run GPU Job
→ Google Cloud Storage bucket
```

Основные ресурсы:

```text
Google Cloud project: fashion-trend-ai
Region: us-central1
Artifact Registry repository: fashion
Docker image: fashion-pipeline-gpu
Cloud Run Job: fashion-pipeline-gpu-job
GPU: NVIDIA L4
Bucket: fashion-trend-ai-runs
Secret: APIFY_API_TOKEN
```

## Подготовка Google Cloud

Авторизация:

```powershell
gcloud auth login
gcloud config set project fashion-trend-ai
```

Включить нужные API:

```powershell
gcloud services enable `
  run.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  secretmanager.googleapis.com `
  storage.googleapis.com `
  aiplatform.googleapis.com
```

Создать Artifact Registry repository, если он ещё не создан:

```powershell
gcloud artifacts repositories create fashion `
  --repository-format=docker `
  --location=us-central1
```

Создать bucket, если он ещё не создан:

```powershell
gcloud storage buckets create gs://fashion-trend-ai-runs `
  --location=us-central1
```

Создать secret для Apify token:

```powershell
gcloud secrets create APIFY_API_TOKEN `
  --replication-policy=automatic
```

Добавить значение секрета:

```powershell
$env:APIFY_API_TOKEN="your_apify_token_here"

echo $env:APIFY_API_TOKEN | gcloud secrets versions add APIFY_API_TOKEN `
  --data-file=-
```

## Cloud Build

Сборка GPU Docker image выполняется из корня репозитория:

```powershell
cd "C:\Users\Ирина Сулла\IdeaProjects\Fashion_predict"
```

Запуск сборки:

```powershell
gcloud builds submit . `
  --config cloudbuild.gpu.yaml
```

После успешной сборки взять digest свежего image:

```powershell
gcloud artifacts docker images list `
  us-central1-docker.pkg.dev/fashion-trend-ai/fashion/fashion-pipeline-gpu `
  --include-tags
```

Digest выглядит так:

```text
sha256:...
```

Для Cloud Run Job лучше использовать не просто тег, а конкретный digest:

```text
us-central1-docker.pkg.dev/fashion-trend-ai/fashion/fashion-pipeline-gpu@sha256:...
```

## Создание Cloud Run GPU Job

Если job ещё не создан:

```powershell
gcloud run jobs create fashion-pipeline-gpu-job `
  --image us-central1-docker.pkg.dev/fashion-trend-ai/fashion/fashion-pipeline-gpu `
  --region us-central1 `
  --memory 16Gi `
  --cpu 4 `
  --gpu 1 `
  --gpu-type nvidia-l4 `
  --no-gpu-zonal-redundancy `
  --task-timeout 3600 `
  --parallelism 1 `
  --max-retries 0 `
  --service-account fashion-pipeline-runner@fashion-trend-ai.iam.gserviceaccount.com `
  --set-env-vars "GCS_BUCKET=fashion-trend-ai-runs,REQUIRE_CUDA=1,GOOGLE_CLOUD_PROJECT=fashion-trend-ai,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash" `
  --set-secrets APIFY_API_TOKEN=APIFY_API_TOKEN:latest
```

Если service account другой, заменить:

```text
fashion-pipeline-runner@fashion-trend-ai.iam.gserviceaccount.com
```

на нужный service account.

## Обновление Cloud Run Job на свежий image

После новой сборки обновить job на конкретный digest:

```powershell
gcloud run jobs update fashion-pipeline-gpu-job `
  --image us-central1-docker.pkg.dev/fashion-trend-ai/fashion/fashion-pipeline-gpu@sha256:YOUR_IMAGE_DIGEST `
  --region us-central1
```

Проверить, какой image использует job:

```powershell
gcloud run jobs describe fashion-pipeline-gpu-job `
  --region us-central1 `
  --format="value(spec.template.spec.template.spec.containers[0].image)"
```

## Переменные окружения Cloud Run Job

Проверить конфигурацию job:

```powershell
gcloud run jobs describe fashion-pipeline-gpu-job `
  --region us-central1 `
  --format=yaml
```

Обновить переменные окружения по одной:

```powershell
gcloud run jobs update fashion-pipeline-gpu-job `
  --region us-central1 `
  --update-env-vars GCS_BUCKET=fashion-trend-ai-runs
```

```powershell
gcloud run jobs update fashion-pipeline-gpu-job `
  --region us-central1 `
  --update-env-vars REQUIRE_CUDA=1
```

```powershell
gcloud run jobs update fashion-pipeline-gpu-job `
  --region us-central1 `
  --update-env-vars GOOGLE_CLOUD_PROJECT=fashion-trend-ai
```

```powershell
gcloud run jobs update fashion-pipeline-gpu-job `
  --region us-central1 `
  --update-env-vars GOOGLE_CLOUD_LOCATION=us-central1
```

```powershell
gcloud run jobs update fashion-pipeline-gpu-job `
  --region us-central1 `
  --update-env-vars GEMINI_MODEL=gemini-2.5-flash
```

## Запуск Cloud Run Job

Полный запуск:

```powershell
gcloud run jobs execute fashion-pipeline-gpu-job `
  --region us-central1 `
  --wait
```

Результаты появятся в bucket:

```text
gs://fashion-trend-ai-runs/runs/<date>/
```

## Очистка run-директории в bucket

Перед повторным запуском можно удалить старый run:

```powershell
gcloud storage rm `
  --recursive `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/**"
```

Если объектов нет, команда может вернуть сообщение, что matching objects не найдены. Это нормально.

## Просмотр Cloud Run executions

```powershell
gcloud run jobs executions list `
  --job fashion-pipeline-gpu-job `
  --region us-central1 `
  --limit=5
```

Описание конкретного execution:

```powershell
gcloud run jobs executions describe EXECUTION_NAME `
  --region us-central1 `
  --format=yaml
```

## Логи Cloud Run Job

Общие логи job:

```powershell
gcloud logging read `
  'resource.type="cloud_run_job" AND resource.labels.job_name="fashion-pipeline-gpu-job"' `
  --limit=300 `
  --order=desc `
  --format="value(textPayload)"
```

Если CLI не показывает логи, открыть `logUri` из команды:

```powershell
gcloud run jobs executions describe EXECUTION_NAME `
  --region us-central1 `
  --format=yaml
```

В поле `status.logUri` будет ссылка на Cloud Logging с правильным фильтром.

## Проверка GPU в логах

При успешном GPU-запуске в логах должны быть строки:

```text
torch cuda available: True
gpu name: NVIDIA L4
Detection device: cuda
GroundingDINO loaded
```

## Работа с Google Cloud Storage

Список файлов run-директории:

```powershell
gcloud storage ls `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/"
```

Список всех файлов рекурсивно:

```powershell
gcloud storage ls `
  --recursive `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/**"
```

Скачать весь run локально:

```powershell
gcloud storage cp `
  --recursive `
  "gs://fashion-trend-ai-runs/runs/2026-06-29" `
  ".\fashion-trend-ai\data\processed\runs\"
```

Скачать только JSON-файлы:

```powershell
gcloud storage cp `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/detections.json" `
  ".\fashion-trend-ai\data\processed\runs\2026-06-29\detections.json"
```

```powershell
gcloud storage cp `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/normalized_posts.json" `
  ".\fashion-trend-ai\data\processed\runs\2026-06-29\normalized_posts.json"
```

```powershell
gcloud storage cp `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/raw_apify_posts.json" `
  ".\fashion-trend-ai\data\processed\runs\2026-06-29\raw_apify_posts.json"
```

Скачать crop-изображения:

```powershell
gcloud storage cp `
  --recursive `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/segmentation/crops" `
  ".\fashion-trend-ai\data\processed\runs\2026-06-29\segmentation\"
```

## Проверка результата

После успешного запуска должны быть файлы:

```text
runs/<date>/raw_apify_posts.json
runs/<date>/normalized_posts.json
runs/<date>/detections.json
runs/<date>/segmentation/segmentations.json
runs/<date>/segmentation/crops/
runs/<date>/fashion_attributes.json
```

Проверить локально:

```powershell
Get-ChildItem .\fashion-trend-ai\data\processed\runs\2026-06-29
```

Проверить в bucket:

```powershell
gcloud storage ls `
  "gs://fashion-trend-ai-runs/runs/2026-06-29/"
```

## Git-команды

Проверить изменения:

```powershell
git status
```

Добавить основные файлы:

```powershell
git add Dockerfile.gpu
git add cloudbuild.gpu.yaml
git add pyproject.toml
git add uv.lock
git add .python-version
git add README.md
git add fashion-trend-ai/app
git add fashion-trend-ai/data/raw/source_urls.txt
git add fashion-trend-ai/data/raw/fashion_taxonomy.json
git add fashion-trend-ai/data/raw/mock_apify_posts.json
git add fashion-trend-ai/.env.example
```

Коммит:

```powershell
git commit -m "Update fashion trend pipeline"
```

Push:

```powershell
git push
```

## Основные артефакты проекта

Для демонстрации результата обычно достаточно показать:

```text
GitHub repository со структурой проекта.
Cloud Build SUCCESS.
Cloud Run GPU Job fashion-pipeline-gpu-job.
Artifact Registry image fashion-pipeline-gpu.
Bucket fashion-trend-ai-runs/runs/<date>/.
detections.json.
segmentations.json.
2–3 crop-изображения из segmentation/crops/.
fashion_attributes.json после завершения Gemini-этапа.
```

## Назначение ключевых файлов

```text
Dockerfile.gpu
Docker image для облачного GPU-запуска pipeline.

cloudbuild.gpu.yaml
Конфигурация Cloud Build для сборки image.

pyproject.toml
Основные зависимости проекта.

uv.lock
Зафиксированные версии зависимостей.

fashion-trend-ai/app/pipeline/run_all.py
Оркестратор pipeline.

fashion-trend-ai/app/pipeline/run_apify.py
Сбор и нормализация Instagram-контента.

fashion-trend-ai/app/pipeline/run_detection.py
Распознавание fashion-объектов через GroundingDINO.

fashion-trend-ai/app/pipeline/run_segmentation.py
Выделение найденных fashion-объектов и сохранение crop-изображений.

fashion-trend-ai/app/pipeline/run_gemini.py
Анализ crop-изображений и формирование fashion-атрибутов.

fashion-trend-ai/app/storage/gcs_storage.py
Выгрузка результатов run-директории в Google Cloud Storage.

fashion-trend-ai/app/taxonomy/fashion_taxonomy.py
Загрузка fashion-категорий и формирование prompt для GroundingDINO.
```
