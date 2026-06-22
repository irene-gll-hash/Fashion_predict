FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY fashion-trend-ai ./fashion-trend-ai
WORKDIR /app/fashion-trend-ai
ENV PYTHONPATH=/app/fashion-trend-ai
CMD ["uv", "run", "python", "-m", "app.pipeline.run_gemini", "--help"]