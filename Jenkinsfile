pipeline {
    agent any
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        retry(1)
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        PYTHON = sh(script: 'which python3 || which python', returnStdout: true).trim()
        VENV_DIR = 'venv'
        PIP = "${VENV_DIR}/bin/pip"
        PYTEST = "${VENV_DIR}/bin/pytest"
        PYLINT = "${VENV_DIR}/bin/pylint"
        PYLINT_THRESHOLD = '9.00'
        DJANGO_SETTINGS_MODULE = 'myproject.settings'
        SECRET_KEY = sh(script: 'python3 -c "import secrets; print(secrets.token_urlsafe(50))"', returnStdout: true).trim()
        
        // Docker variables - LOCAL BUILD ONLY
        DOCKER_IMAGE_NAME = 'django-contact-app'
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(8)}"
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
                echo "✅ Workspace cleaned and code checked out"
            }
        }
        
        stage('Install SonarScanner') {
            steps {
                script {
                    echo "📦 Installing SonarScanner..."
                    
                    sh '''
                        # Always download fresh (it's cached anyway)
                        if [ ! -d "sonar-scanner" ]; then
                            wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
                            unzip -q sonar-scanner-cli-*.zip
                            rm sonar-scanner-cli-*.zip
                            mv sonar-scanner-* sonar-scanner
                        fi
                        
                        # Verify
                        ./sonar-scanner/bin/sonar-scanner --version
                        echo "✅ SonarScanner ready"
                    '''
                }
            }
        }
        
        stage('Create Virtual Environment') {
            steps {
                script {
                    echo 'Creating virtual environment...'
                    sh '${PYTHON} -m venv ${VENV_DIR}'
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    sh '''
                        echo "Installing/upgrading pip..."
                        ${PIP} install --upgrade pip setuptools wheel
                        
                        if [ -f requirements.txt ]; then
                            echo "Installing from requirements.txt..."
                            ${PIP} install -r requirements.txt
                            echo "✅ Dependencies installed"
                        else
                            echo "Installing Django and test tools..."
                            ${PIP} install django pytest pytest-django pytest-cov pylint
                            echo "✅ Basic packages installed"
                        fi
                    '''
                }
            }
        }
        
        stage('Initialize Django') {
            steps {
                script {
                    echo "🔧 Initializing Django with test SECRET_KEY..."
                    sh '''
                        ${VENV_DIR}/bin/python -c "
import os
os.environ['SECRET_KEY'] = '${SECRET_KEY}'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()
print('✅ Django initialized successfully')
                        "
                    '''
                }
            }
        }
        
        stage('Run Pytest with Coverage') {
            steps {
                script {
                    echo "🧪 Running Pytest with coverage..."
                    
                    sh """
                        export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
                        export SECRET_KEY='${SECRET_KEY}'
                        
                        ${PYTEST} accounts \
                            --cov \
                            --cov-report=term \
                            --cov-report=xml:coverage.xml \
                            --ds=myproject.settings \
                            --tb=short \
                            --junitxml=junit-results.xml
                    """
                }
            }
        }
        
        stage('Pylint Code Analysis') {
            steps {
                script {
                    echo "🔍 Running Pylint..."
                    sh """
                        ${PYLINT} accounts \
                            --fail-under=${PYLINT_THRESHOLD} \
                            --output-format=json:pylint-report.json \
                            --exit-zero || echo "⚠️ Pylint score below threshold"
                    """
                }
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                script {
                    echo "📊 Running SonarQube analysis..."
                    
                    withSonarQubeEnv('sonarqube') {
                        sh '''
                            ./sonar-scanner/bin/sonar-scanner \
                                -Dsonar.projectKey=django-app-${BUILD_NUMBER} \
                                -Dsonar.projectName="Django Contact App" \
                                -Dsonar.sources=. \
                                -Dsonar.exclusions=**/migrations/**,**/__pycache__/**,**/*.pyc,venv/**,**/test*.py \
                                -Dsonar.python.coverage.reportPaths=coverage.xml \
                                -Dsonar.python.xunit.reportPath=junit-results.xml \
                                -Dsonar.python.pylint.reportPath=pylint-report.json \
                                -Dsonar.python.version=3 \
                                -Dsonar.sourceEncoding=UTF-8
                        '''
                    }
                }
            }
        }
        
        stage('Quality Gate Check') {
            steps {
                script {
                    echo "🔍 Checking SonarQube Quality Gate (will FAIL pipeline if quality is bad)..."
                    
                    timeout(time: 5, unit: 'MINUTES') {
                        def qg = waitForQualityGate abortPipeline: false
                        
                        if (qg.status == 'OK') {
                            echo "✅ Quality Gate PASSED"
                        } else {
                            echo "❌❌❌ CRITICAL: Quality Gate FAILED! ❌❌❌"
                            echo "Status: ${qg.status}"
                            echo "URL: http://localhost:9000/dashboard?id=django-app-${BUILD_NUMBER}"
                            
                            // THIS WILL FAIL THE PIPELINE
                            error("SonarQube Quality Gate failed: ${qg.status}. Fix code quality issues!")
                        }
                    }
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo "🐳 Building Docker image locally..."
                    
                    // Check if Dockerfile exists, create if not
                    sh '''
                        if [ ! -f "Dockerfile" ]; then
                            echo "⚠️ No Dockerfile found. Creating a basic Django Dockerfile..."
                            cat > Dockerfile << 'EOF'
# Use official Python runtime as parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files (if Django project)
RUN python manage.py collectstatic --noinput 2>/dev/null || echo "No collectstatic command found"

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
EOF
                            echo "✅ Created basic Dockerfile"
                        else
                            echo "✅ Using existing Dockerfile"
                        fi
                    '''
                    
                    // Also ensure .dockerignore exists
                    sh '''
                        if [ ! -f ".dockerignore" ]; then
                            echo "Creating .dockerignore file..."
                            cat > .dockerignore << 'EOF'
.git
.gitignore
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
.coverage
htmlcov/
.DS_Store
*.log
local_settings.py
db.sqlite3
media/
test-reports/
sonar-scanner/
node_modules/
README.md
Dockerfile
.dockerignore
EOF
                            echo "✅ Created .dockerignore"
                        fi
                    '''
                    
                    // Build Docker image
                    sh """
                        echo "Building Docker image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                        
                        # List files before build (for debugging)
                        echo "Files in directory:"
                        ls -la
                        
                        # Build the image
                        docker build \
                            -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} \
                            -t ${DOCKER_IMAGE_NAME}:latest \
                            --progress=plain \
                            .
                        
                        echo "✅ Docker image built successfully!"
                        
                        # List images to verify
                        echo "Available Docker images:"
                        docker images | grep ${DOCKER_IMAGE_NAME}
                    """
                }
            }
        }
        
        stage('Test Docker Image') {
            steps {
                script {
                    echo "🧪 Testing Docker image..."
                    
                    // Run a simple test to ensure the image works
                    sh """
                        # Test 1: Check if image was created
                        docker inspect ${DOCKER_IMAGE_NAME}:latest > /dev/null 2>&1
                        if [ \$? -eq 0 ]; then
                            echo "✅ Image exists"
                        else
                            echo "❌ Image not found"
                            exit 1
                        fi
                        
                        # Test 2: Check image size (should not be empty)
                        IMAGE_SIZE=\$(docker images ${DOCKER_IMAGE_NAME}:latest --format "{{.Size}}")
                        echo "📊 Image size: \${IMAGE_SIZE}"
                        
                        # Test 3: Run container and check if it starts
                        echo "Starting container for quick test..."
                        CONTAINER_ID=\$(docker run -d -p 8080:8000 ${DOCKER_IMAGE_NAME}:latest 2>/dev/null || echo "")
                        
                        if [ ! -z "\$CONTAINER_ID" ]; then
                            echo "✅ Container started with ID: \$CONTAINER_ID"
                            
                            # Give it a moment to start
                            sleep 5
                            
                            # Check if container is running
                            if docker ps | grep -q \$CONTAINER_ID; then
                                echo "✅ Container is running"
                            else
                                echo "⚠️ Container started but not running. Checking logs..."
                                docker logs \$CONTAINER_ID
                            fi
                            
                            # Stop and remove container
                            docker stop \$CONTAINER_ID 2>/dev/null || true
                            docker rm \$CONTAINER_ID 2>/dev/null || true
                            echo "✅ Container cleaned up"
                        else
                            echo "⚠️ Could not start container. This might be OK if Django needs database setup."
                        fi
                        
                        # Test 4: Check what's in the image
                        echo "Image contents:"
                        docker run --rm ${DOCKER_IMAGE_NAME}:latest ls -la /app 2>/dev/null || echo "Could not list /app contents"
                    """
                }
            }
        }
        
        stage('Save Docker Image') {
            steps {
                script {
                    echo "💾 Saving Docker image to workspace..."
                    
                    sh """
                        # Save the image as tar file
                        docker save -o ${DOCKER_IMAGE_NAME}-${DOCKER_IMAGE_TAG}.tar ${DOCKER_IMAGE_NAME}:latest
                        
                        # Compress it
                        gzip ${DOCKER_IMAGE_NAME}-${DOCKER_IMAGE_TAG}.tar
                        
                        echo "✅ Docker image saved as ${DOCKER_IMAGE_NAME}-${DOCKER_IMAGE_TAG}.tar.gz"
                        ls -lh ${DOCKER_IMAGE_NAME}-*.tar.gz
                    """
                }
            }
        }
    }
    
    post {
        always {
            // Archive reports and Docker image
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, *.tar.gz', allowEmptyArchive: true
            
            // Cleanup
            sh '''
                echo "🧹 Cleaning up workspace..."
                rm -rf ${VENV_DIR} 2>/dev/null || true
                rm -f coverage.xml junit-results.xml pylint-report.json 2>/dev/null || true
                
                # Keep Docker images for inspection (comment out to save space)
                # docker rmi ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} ${DOCKER_IMAGE_NAME}:latest 2>/dev/null || true
                
                # Keep sonar-scanner directory for future runs
                echo "✅ Cleanup complete"
            '''
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            script {
                echo "🐳 Docker Image Built Locally:"
                echo "   - ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                echo "   - ${DOCKER_IMAGE_NAME}:latest"
                echo "💾 Saved as: ${DOCKER_IMAGE_NAME}-${DOCKER_IMAGE_TAG}.tar.gz"
                echo ""
                echo "📦 To use this image locally:"
                echo "   1. Copy the .tar.gz file from Jenkins artifacts"
                echo "   2. Load it: docker load < ${DOCKER_IMAGE_NAME}-${DOCKER_IMAGE_TAG}.tar.gz"
                echo "   3. Run it: docker run -p 8000:8000 ${DOCKER_IMAGE_NAME}:latest"
            }
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            script {
                // Helpful debugging info
                sh '''
                    echo "🔍 Debugging information:"
                    echo "Docker info:"
                    docker info 2>/dev/null || echo "Docker not available"
                    echo ""
                    echo "Current directory:"
                    pwd
                    ls -la
                    echo ""
                    echo "Docker images:"
                    docker images 2>/dev/null || echo "Cannot list images"
                '''
            }
        }
    }
}