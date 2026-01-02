@echo off
set /p DOCKER_USER="Enter your Docker Hub Username: "
set IMAGE_NAME=%DOCKER_USER%/comfyui-runpod-android:latest

echo Building Image: %IMAGE_NAME%
echo This may take a while...
docker build -t %IMAGE_NAME% .

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo Pushing Image to Docker Hub...
docker push %IMAGE_NAME%

if %errorlevel% neq 0 (
    echo Push failed! Make sure you are logged in with 'docker login'
    pause
    exit /b %errorlevel%
)

echo Done! Image: %IMAGE_NAME%
pause
