pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
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
        
        // Docker Hub configuration
        DOCKER_IMAGE_NAME = 'tasnimelleuchenis/django-contact-app'
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        
        // Docker retry configuration
        DOCKER_PULL_RETRIES = '3'
        DOCKER_PULL_DELAY = '5'
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
                        if [ ! -d "sonar-scanner" ]; then
                            wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
                            unzip -q sonar-scanner-cli-*.zip
                            rm sonar-scanner-cli-*.zip
                            mv sonar-scanner-* sonar-scanner
                        fi
                        
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
                        
                        ${PIP} install pylint-pytest
                        
                        if [ -f requirements.txt ]; then
                            echo "Installing from requirements.txt..."
                            ${PIP} install -r requirements.txt
                            echo "✅ Dependencies installed"
                        else
                            echo "Installing Django and test tools..."
                            ${PIP} install django pytest pytest-django pytest-cov pylint pylint-pytest
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
                            --output-format=json:pylint-report.json \
                            --exit-zero || echo "Pylint analysis completed"
                        
                        if [ -f pylint-report.json ]; then
                            echo "✅ Pylint report created successfully"
                        else
                            echo "⚠️ Pylint report not created"
                        fi
                    """
                }
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                script {
                    echo "📊 Running SonarQube analysis..."
                    
                    def projectKey = "django-app-${env.BUILD_NUMBER}"
                    
                    withSonarQubeEnv('sonarqube') {
                        sh """
                            cat > sonar-project.properties << EOF
sonar.projectKey=${projectKey}
sonar.projectName=Django Contact App Build ${env.BUILD_NUMBER}
sonar.projectVersion=${env.BUILD_NUMBER}
sonar.sources=.
sonar.exclusions=**/migrations/**,**/__pycache__/**,**/*.pyc,venv/**,**/.git/**,coverage.xml,junit-results.xml,pylint-report.json
sonar.tests=.
sonar.test.inclusions=**/test*.py,**/tests/**
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=junit-results.xml
sonar.python.pylint.reportPaths=pylint-report.json
sonar.python.version=3
sonar.sourceEncoding=UTF-8
sonar.qualitygate.wait=true
sonar.qualitygate.timeout=300
EOF

                            ./sonar-scanner/bin/sonar-scanner \
                                -Dsonar.host.url=${SONAR_HOST_URL} \
                                -Dsonar.login=${SONAR_AUTH_TOKEN} \
                                -Dproject.settings=sonar-project.properties
                        """
                    }
                }
            }
        }
        
        stage('Quality Gate Check') {
            steps {
                script {
                    echo "🔍 Checking SonarQube Quality Gate..."
                    
                    timeout(time: 5, unit: 'MINUTES') {
                        try {
                            def qg = waitForQualityGate(abortPipeline: false)
                            
                            if (qg.status == 'OK') {
                                echo "✅ Quality Gate PASSED"
                            } else {
                                echo "⚠️ Quality Gate FAILED with status: ${qg.status}"
                            }
                        } catch (Exception e) {
                            echo "⚠️ Could not retrieve Quality Gate status: ${e.message}"
                        }
                    }
                }
            }
        }
        
        stage('Docker Build and Push') {
            when {
                expression { fileExists('Dockerfile') }
                expression { env.DOCKER_IMAGE_NAME }
            }
            environment {
                DOCKER_HUB_CREDS = credentials('docker-hub-credentials')
            }
            steps {
                script {
                    echo "🐳 Building Docker image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    
                    // Retry pulling base image with exponential backoff
                    sh '''
                        echo "Pulling base image with retries..."
                        BASE_IMAGE=$(grep -i "^FROM" Dockerfile | head -1 | cut -d' ' -f2)
                        
                        for i in $(seq 1 ${DOCKER_PULL_RETRIES}); do
                            echo "Attempt $i of ${DOCKER_PULL_RETRIES} to pull ${BASE_IMAGE}..."
                            if docker pull ${BASE_IMAGE}; then
                                echo "✅ Base image pulled successfully"
                                break
                            else
                                if [ $i -eq ${DOCKER_PULL_RETRIES} ]; then
                                    echo "❌ Failed to pull base image after ${DOCKER_PULL_RETRIES} attempts"
                                    exit 1
                                fi
                                echo "Pull failed, waiting ${DOCKER_PULL_DELAY} seconds before retry..."
                                sleep ${DOCKER_PULL_DELAY}
                            fi
                        done
                    '''
                    
                    // Build Docker image
                    sh """
                        docker build \
                            --build-arg BUILD_NUMBER=${env.BUILD_NUMBER} \
                            --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                            --build-arg VCS_REF=\$(git rev-parse --short HEAD) \
                            -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} \
                            -t ${DOCKER_IMAGE_NAME}:latest \
                            .
                    """
                    
                    echo "✅ Docker image built: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    
                    echo "📤 Pushing Docker images to Docker Hub..."
                    
                    // Login and push
                    sh '''
                        echo "Logging into Docker Hub..."
                        echo "$DOCKER_HUB_CREDS_PSW" | docker login -u "$DOCKER_HUB_CREDS_USR" --password-stdin
                        
                        echo "Pushing ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}..."
                        docker push ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}
                        
                        echo "Pushing ${DOCKER_IMAGE_NAME}:latest..."
                        docker push ${DOCKER_IMAGE_NAME}:latest
                        
                        docker logout
                        
                        echo "✅ Docker images successfully pushed to Docker Hub:"
                        echo "   - ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}"
                        echo "   - ${DOCKER_IMAGE_NAME}:latest"
                    '''
                }
            }
            post {
                failure {
                    echo "❌ Docker build or push failed"
                    sh 'docker logout || true'
                }
                success {
                    echo "✅ Docker build and push completed successfully"
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
                expression { env.DOCKER_IMAGE_NAME }
                expression { currentBuild.result != 'FAILURE' }
            }
            steps {
                script {
                    echo "🚀 Deploying to staging environment..."
                    
                    sh """
                        # Pull the latest image
                        echo "Pulling image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                        docker pull ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        
                        # Stop and remove old container
                        echo "Stopping existing container..."
                        docker stop django-staging || true
                        docker rm django-staging || true
                        
                        # Run new container
                        echo "Starting new container..."
                        docker run -d \
                            --name django-staging \
                            -p 8000:8000 \
                            -e DJANGO_ENV=staging \
                            -e SECRET_KEY=${SECRET_KEY} \
                            --restart unless-stopped \
                            ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        
                        # Wait for container to start
                        sleep 5
                        
                        # Check if container is running
                        if [ "\$(docker ps -q -f name=django-staging)" ]; then
                            echo "✅ Container is running!"
                            echo "📋 Container logs:"
                            docker logs --tail 20 django-staging
                            echo ""
                            echo "🌐 Application is available at: http://localhost:8000"
                        else
                            echo "❌ Container failed to start"
                            echo "📋 Last logs:"
                            docker logs django-staging
                            exit 1
                        fi
                    """
                }
            }
            post {
                failure {
                    echo "❌ Failed to deploy to staging"
                    sh 'docker logs django-staging || true'
                }
                success {
                    echo "✅ Successfully deployed to staging environment"
                }
            }
        }
    }
    
    post {
        always {
            // Archive reports
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, sonar-project.properties, .scannerwork/report-task.txt', allowEmptyArchive: true
            
            // Display SonarQube URL
            script {
                if (fileExists('.scannerwork/report-task.txt')) {
                    def reportTask = readFile('.scannerwork/report-task.txt')
                    
                    def extractValue = { key ->
                        def matcher = reportTask =~ /${key}=(.*)/
                        return matcher.find() ? matcher.group(1) : null
                    }
                    
                    def dashboardUrl = extractValue('dashboardUrl')
                    if (dashboardUrl) {
                        echo "SonarQube Analysis URL: ${dashboardUrl}"
                    }
                }
            }
            
            // Don't cleanup the container, keep it running!
            echo "✅ Staging container 'django-staging' is still running"
            
            // Cleanup only build artifacts
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json || true
            '''
            
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
            echo "Staging URL: http://localhost:8000"
            echo "View on Docker Hub: https://hub.docker.com/r/${env.DOCKER_IMAGE_NAME}/tags"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "Check the logs above for details"
        }
        
        unstable {
            echo "⚠️⚠️⚠️ PIPELINE UNSTABLE ⚠️⚠️⚠️"
        }
    }
}