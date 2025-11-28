$ErrorActionPreference = "Stop"
# Navigate to backend root (parent of scripts folder)
Push-Location "$PSScriptRoot\.."

# Check for Docker and start services
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    Write-Host "Starting Docker services (db, redis)..."
    try {
        # docker-compose.yml is in the project root (one level up from backend)
        docker compose -f ..\docker-compose.yml up -d db redis
    } catch {
        Write-Warning "Failed to start Docker services. Please ensure Docker Desktop is running."
    }
} else {
    Write-Warning "Docker command not found. Please ensure PostgreSQL and Redis are running manually."
}

Write-Host "Checking virtual environment..."
if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing/Updating requirements..."
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Starting Uvicorn..."
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

Pop-Location
