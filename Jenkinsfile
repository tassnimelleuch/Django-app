pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')  // Increased timeout for Docker pushes
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
        
        DOCKER_IMAGE_NAME = 'tasnimelleuchenis/django-contact-app'
        
        // CLEAN FORMAT: 2026-02-16-at-10-17-27-62 (Docker-safe: only lowercase, numbers, hyphens)
        DOCKER_IMAGE_TAG = sh(script: '''#!/bin/bash
            export LANG=C
            date "+%Y-%m-%d-at-%H-%M-%S-build-${BUILD_NUMBER}" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g'
        ''', returnStdout: true).trim()
        
        // For display purposes only (not used in tags)
        HUMAN_READABLE_DATE = sh(script: '''#!/bin/bash
            export LANG=C
            date "+%Y-%m-%d at %H:%M:%S"
        ''', returnStdout: true).trim()
        
        DOCKER_PULL_RETRIES = '5'        // Increased retries
        DOCKER_PULL_DELAY = '10'         // Increased delay
        DOCKER_PUSH_RETRIES = '5'         // Max push retries
        DOCKER_PUSH_DELAY = '15'          // Delay between push retries
        DOCKER_PUSH_TIMEOUT = '300'       // 5 minutes per push attempt
        
        // SonarCloud configuration
        SONAR_ORGANIZATION = 'tasnimelleuchenis'  // Replace with your GitHub username/organization
        SONAR_PROJECT_KEY = "django-contact-app-${BUILD_NUMBER}"
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
                echo "✅ Workspace cleaned and code checked out"
                script {
                    echo "🏷️ Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
                    echo "🐳 Docker tag: ${DOCKER_IMAGE_TAG}"
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
        
        stage('SonarCloud Analysis') {
    steps {
        script {
            def dateKey = sh(script: '''#!/bin/bash
                export LANG=C
                date "+%Y-%m-%d-%H-%M-%S"
            ''', returnStdout: true).trim()
            
            def projectKey = "django-contact-app-${dateKey}-build-${env.BUILD_NUMBER}"
            def projectName = "Django Contact App ${dateKey} (#${env.BUILD_NUMBER})"
            
            echo "📊 Running SonarCloud analysis for: ${projectName}"
            
            withSonarQubeEnv('sonarcloud') {
                def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                
                withEnv(["PATH+SCANNER=${scannerHome}/bin"]) {
                    withCredentials([string(credentialsId: 'sonar-cloud', variable: 'SONAR_TOKEN')]) {
                        sh """
                            sonar-scanner \
                                -Dsonar.projectKey=${projectKey} \
                                -Dsonar.organization=tassnimelleuch \
                                -Dsonar.projectName="${projectName}" \
                                -Dsonar.projectVersion=${dateKey} \
                                -Dsonar.sources=. \
                                -Dsonar.exclusions=**/migrations/**,**/__pycache__/**,**/*.pyc,venv/**,**/.git/**,coverage.xml,junit-results.xml,pylint-report.json \
                                -Dsonar.tests=. \
                                -Dsonar.test.inclusions=**/test*.py,**/tests/** \
                                -Dsonar.python.coverage.reportPaths=coverage.xml \
                                -Dsonar.python.xunit.reportPath=junit-results.xml \
                                -Dsonar.python.pylint.reportPaths=pylint-report.json \
                                -Dsonar.python.version=3 \
                                -Dsonar.sourceEncoding=UTF-8 \
                                -Dsonar.host.url=https://sonarcloud.io \
                                -Dsonar.token=\${SONAR_TOKEN} \
                                -Dsonar.qualitygate.wait=true \
                                -Dsonar.qualitygate.timeout=300
                        """
                    }
                }
            }
        }
    }
} 
        
        stage('Quality Gate Check') {
            steps {
                script {
                    echo "🔍 Checking SonarCloud Quality Gate..."
                    
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
                    echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
                    echo "⏱️ This may take several minutes depending on network speed..."
                    
                    sh '''
                        echo "Pulling base image with retries..."
                        BASE_IMAGE=$(grep -i "^FROM" Dockerfile | head -1 | cut -d' ' -f2)
                        
                        for i in $(seq 1 ${DOCKER_PULL_RETRIES}); do
                            echo "Attempt $i of ${DOCKER_PULL_RETRIES} to pull ${BASE_IMAGE}..."
                            if timeout 300 docker pull ${BASE_IMAGE}; then
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
                    
                    sh """
                        docker build \
                            --build-arg BUILD_NUMBER=${env.BUILD_NUMBER} \
                            --build-arg BUILD_DATE="\$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
                            --build-arg VCS_REF="\$(git rev-parse --short HEAD)" \
                            --build-arg BUILD_TAG="${env.DOCKER_IMAGE_TAG}" \
                            --build-arg HUMAN_DATE="${env.HUMAN_READABLE_DATE}" \
                            -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} \
                            -t ${DOCKER_IMAGE_NAME}:latest \
                            .
                    """
                    
                    echo "✅ Docker image built: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    echo "📤 Pushing Docker images to Docker Hub (this may take 5-10 minutes)..."
                    
                    sh '''
                        echo "Logging into Docker Hub..."
                        echo "$DOCKER_HUB_CREDS_PSW" | docker login -u "$DOCKER_HUB_CREDS_USR" --password-stdin
                        
                        # Function to push with retry and timeout
                        push_with_retry() {
                            local IMAGE=$1
                            local TAG=$2
                            local MAX_RETRIES=${DOCKER_PUSH_RETRIES}
                            local DELAY=${DOCKER_PUSH_DELAY}
                            local TIMEOUT=${DOCKER_PUSH_TIMEOUT}
                            
                            for i in $(seq 1 ${MAX_RETRIES}); do
                                echo "Push attempt $i of ${MAX_RETRIES} for ${IMAGE}:${TAG}..."
                                
                                # Use timeout command to prevent infinite hangs
                                if timeout ${TIMEOUT} docker push ${IMAGE}:${TAG}; then
                                    echo "✅ Successfully pushed ${IMAGE}:${TAG}"
                                    return 0
                                else
                                    EXIT_CODE=$?
                                    if [ $i -eq ${MAX_RETRIES} ]; then
                                        echo "❌ Failed to push after ${MAX_RETRIES} attempts"
                                        return 1
                                    fi
                                    
                                    if [ ${EXIT_CODE} -eq 124 ]; then
                                        echo "⚠️ Push timed out after ${TIMEOUT} seconds"
                                    else
                                        echo "⚠️ Push failed with error code ${EXIT_CODE}"
                                    fi
                                    
                                    echo "Waiting ${DELAY} seconds before retry..."
                                    sleep ${DELAY}
                                fi
                            done
                        }
                        
                        # Push both tags with retry logic
                        push_with_retry "${DOCKER_IMAGE_NAME}" "${DOCKER_IMAGE_TAG}" || exit 1
                        push_with_retry "${DOCKER_IMAGE_NAME}" "latest" || exit 1
                        
                        docker logout
                        
                        echo "✅✅✅ DOCKER PUSH COMPLETED SUCCESSFULLY! ✅✅✅"
                        echo "   - ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                        echo "   - ${DOCKER_IMAGE_NAME}:latest"
                    '''
                }
            }
            post {
                failure {
                    echo "❌❌❌ DOCKER BUILD OR PUSH FAILED AFTER MULTIPLE RETRIES ❌❌❌"
                    echo "This could be due to network issues or Docker Hub being slow."
                    echo "The build will continue but without Docker push."
                    sh 'docker logout || true'
                }
                success {
                    echo "✅ Docker build and push completed successfully"
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, sonar-project.properties, .scannerwork/report-task.txt', allowEmptyArchive: true
            
            script {
                if (fileExists('.scannerwork/report-task.txt')) {
                    def reportTask = readFile('.scannerwork/report-task.txt')
                    
                    def extractValue = { key ->
                        def matcher = reportTask =~ /${key}=(.*)/
                        return matcher.find() ? matcher.group(1) : null
                    }
                    
                    def dashboardUrl = extractValue('dashboardUrl')
                    if (dashboardUrl) {
                        echo "SonarCloud Analysis URL: ${dashboardUrl}"
                        echo "Project: Django Contact App ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
                    }
                }
            }
            
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json || true
            '''
            
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "🐳 Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
            echo "☁️ SonarCloud: Django Contact App ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "📦 View on Docker Hub: https://hub.docker.com/r/${env.DOCKER_IMAGE_NAME}/tags"
            echo "📊 View on SonarCloud: https://sonarcloud.io/project/overview?id=django-contact-app-${env.BUILD_NUMBER}"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "Check the logs above for details"
        }
        
        unstable {
            echo "⚠️⚠️⚠️ PIPELINE UNSTABLE ⚠️⚠️⚠️"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
        }
    }
}