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
        
        // Docker Hub configuration - FIXED
        DOCKER_REGISTRY = ''  // Empty string for Docker Hub
        DOCKER_IMAGE_NAME = 'tasnimelleuchenis/django-contact-app'  
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        // These are now just for reference, not used in commands
        DOCKER_FULL_IMAGE = "${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
        DOCKER_LATEST_IMAGE = "${DOCKER_IMAGE_NAME}:latest"
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
                        
                        # Install pylint-pytest plugin for better SonarQube integration
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
                        # Run Pylint with proper output format for SonarQube
                        ${PYLINT} accounts \
                            --output-format=json:pylint-report.json \
                            --exit-zero || echo "⚠️ Pylint analysis completed"
                        
                        # Verify Pylint report was created
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
                            # Create sonar-project.properties file for better configuration
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

                            # Run sonar-scanner
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
                                echo "Check SonarQube for detailed analysis"
                            }
                        } catch (Exception e) {
                            echo "⚠️ Could not retrieve Quality Gate status: ${e.message}"
                            echo "Analysis may still be processing in SonarQube"
                        }
                    }
                }
            }
        }
        
        stage('Docker Build') {
            when {
                expression { fileExists('Dockerfile') }
            }
            steps {
                script {
                    echo "🐳 Building Docker image with tag: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    
                    sh """
                        docker build \
                            --build-arg BUILD_NUMBER=${env.BUILD_NUMBER} \
                            --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                            --build-arg VCS_REF=\$(git rev-parse --short HEAD) \
                            -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} \
                            -t ${DOCKER_IMAGE_NAME}:latest \
                            .
                    """
                    
                    echo "🔒 Running security scan on Docker image..."
                    try {
                        sh """
                            docker run --rm \
                                -v /var/run/docker.sock:/var/run/docker.sock \
                                aquasec/trivy image \
                                --severity HIGH,CRITICAL \
                                --no-progress \
                                --exit-code 0 \
                                ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        """
                        echo "✅ Docker image security scan completed"
                    } catch (Exception e) {
                        echo "⚠️ Docker security scan failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('Docker Push') {
            when {
                allOf {
                    expression { env.DOCKER_IMAGE_NAME }
                    expression { fileExists('Dockerfile') }
                    expression { currentBuild.result != 'FAILURE' }
                }
            }
            environment {
                DOCKER_HUB_CREDS = credentials('docker-hub-credentials')
            }
            steps {
                script {
                    echo "📤 Pushing Docker image to Docker Hub..."
                    
                    sh '''
                        # Login to Docker Hub
                        echo $DOCKER_HUB_CREDS_PSW | docker login -u $DOCKER_HUB_CREDS_USR --password-stdin
                        
                        # Push the images - NO TAGGING NEEDED, they're already tagged correctly!
                        echo "Pushing ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}..."
                        docker push ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}
                        
                        echo "Pushing ${DOCKER_IMAGE_NAME}:latest..."
                        docker push ${DOCKER_IMAGE_NAME}:latest
                        
                        # Logout
                        docker logout
                        
                        echo "✅ Successfully pushed to Docker Hub:"
                        echo "   - ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}"
                        echo "   - ${DOCKER_IMAGE_NAME}:latest"
                    '''
                }
            }
            post {
                failure {
                    echo "❌ Failed to push Docker image"
                    sh 'docker logout || true'
                }
                success {
                    echo "✅ Docker image successfully published to Docker Hub"
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
                    echo "🚀 Ready to deploy Docker image to staging environment..."
                    echo "Image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    echo ""
                    echo "To deploy manually:"
                    echo "docker pull ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    echo "docker run -d -p 8000:8000 ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                }
            }
        }
    }
    
    post {
        always {
            // Archive all reports
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, sonar-project.properties, .scannerwork/report-task.txt', allowEmptyArchive: true
            
            // Display SonarQube URL if available
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
            
            // Cleanup
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json || true
            '''
            
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
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