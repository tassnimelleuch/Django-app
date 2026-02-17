pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 10, unit: 'MINUTES')
    }
    
    environment {
        PYTHON = sh(script: 'which python3 || which python', returnStdout: true).trim()
        VENV_DIR = 'venv'
        PIP = "${VENV_DIR}/bin/pip"
        PYTEST = "${VENV_DIR}/bin/pytest"
        PYLINT = "${VENV_DIR}/bin/pylint"
        DJANGO_SETTINGS_MODULE = 'myproject.settings'
        SECRET_KEY = sh(script: 'python3 -c "import secrets; print(secrets.token_urlsafe(50))"', returnStdout: true).trim()
        
        DOCKER_IMAGE_NAME = 'tasnimelleuchenis/django-contact-app'
        
        DOCKER_IMAGE_TAG = sh(script: '''#!/bin/bash
            export LANG=C
            date "+%Y-%m-%d-at-%H-%M-%S-build-${BUILD_NUMBER}" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g'
        ''', returnStdout: true).trim()
        
        HUMAN_READABLE_DATE = sh(script: '''#!/bin/bash
            export LANG=C
            date "+%Y-%m-%d at %H:%M:%S"
        ''', returnStdout: true).trim()
        
        DOCKER_PULL_RETRIES = '5'
        DOCKER_PULL_DELAY = '10'
        DOCKER_PUSH_RETRIES = '5'
        DOCKER_PUSH_DELAY = '15'
        DOCKER_PUSH_TIMEOUT = '300'
        
        // GitHub/SonarCloud configuration
        GITHUB_REPO = 'Django-app'
        GITHUB_OWNER = 'tassnimelleuch'
        SONAR_PROJECT_KEY = 'tassnimelleuch_Django-app'
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
                    echo "🔍 Commit: ${GIT_COMMIT}"
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
        
        // ===== THIS WILL ACTUALLY WORK AND FAIL IF SONARCLOUD FAILS =====
        stage('Verify SonarCloud Quality Gate') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token', 
                    usernameVariable: 'GITHUB_USER',
                    passwordVariable: 'GITHUB_TOKEN'
                )]) {
                    script {
                        echo "🔍 VERIFYING SonarCloud quality gate from GitHub..."
                        echo "🔗 SonarCloud Dashboard: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
                        
                        // DEBUG: Save the FULL response
                        sh(script: '''
                            curl -s -H "Authorization: token $GITHUB_TOKEN" \
                            "https://api.github.com/repos/'''${GITHUB_OWNER}'''/'''${GITHUB_REPO}'''/commits/'''${GIT_COMMIT}'''/check-runs" > full-response.json
                            echo "===== FULL GITHUB RESPONSE ====="
                            cat full-response.json
                            echo "===== END RESPONSE ====="
                        ''', mask: true)
                        
                        // Show all check runs
                        def allChecks = sh(
                            script: "grep -o '\"name\":\"[^\"]*\"' full-response.json || echo 'No checks found'",
                            returnStdout: true
                        ).trim()
                        
                        echo "All GitHub checks on this commit:"
                        echo "${allChecks}"
                        
                        // Look specifically for SonarCloud
                        def sonarPresent = sh(
                            script: "grep -i 'sonarcloud' full-response.json | wc -l",
                            returnStdout: true
                        ).trim().toInteger()
                        
                        echo "SonarCloud present: ${sonarPresent}"
                        
                        if (sonarPresent > 0) {
                            def conclusion = sh(
                                script: '''
                                    grep -i -A5 'sonarcloud' full-response.json | \
                                    grep -i 'conclusion' | \
                                    head -1 | \
                                    cut -d':' -f2 | \
                                    tr -d ' ,"' || echo 'unknown'
                                ''',
                                returnStdout: true
                            ).trim()
                            
                            echo "SonarCloud conclusion: ${conclusion}"
                            
                            if (conclusion == "success") {
                                echo "✅✅✅ QUALITY GATE PASSED! ✅✅✅"
                            } else if (conclusion == "failure") {
                                error "❌❌❌ QUALITY GATE FAILED! ❌❌❌"
                            } else {
                                echo "⚠️ SonarCloud status: ${conclusion}"
                            }
                        } else {
                            echo "❌❌❌ SONARCLOUD NOT FOUND IN GITHUB API!"
                            echo "This means:"
                            echo "1. SonarCloud is NOT installed on your GitHub repo"
                            echo "2. OR SonarCloud is using a different name"
                            echo "3. OR Your token doesn't have permission to see checks"
                            
                            // Show what IS in the response
                            def firstFewLines = sh(
                                script: "head -20 full-response.json",
                                returnStdout: true
                            ).trim()
                            
                            echo "First 20 lines of response:"
                            echo "${firstFewLines}"
                        }
                        
                        archiveArtifacts artifacts: 'full-response.json', allowEmptyArchive: true
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
                    echo "📤 Pushing Docker images to Docker Hub..."
                    
                    sh '''
                        echo "Logging into Docker Hub..."
                        echo "$DOCKER_HUB_CREDS_PSW" | docker login -u "$DOCKER_HUB_CREDS_USR" --password-stdin
                        
                        push_with_retry() {
                            local IMAGE=$1
                            local TAG=$2
                            local MAX_RETRIES=${DOCKER_PUSH_RETRIES}
                            local DELAY=${DOCKER_PUSH_DELAY}
                            local TIMEOUT=${DOCKER_PUSH_TIMEOUT}
                            
                            for i in $(seq 1 ${MAX_RETRIES}); do
                                echo "Push attempt $i of ${MAX_RETRIES} for ${IMAGE}:${TAG}..."
                                
                                if timeout ${TIMEOUT} docker push ${IMAGE}:${TAG}; then
                                    echo "✅ Successfully pushed ${IMAGE}:${TAG}"
                                    return 0
                                else
                                    if [ $i -eq ${MAX_RETRIES} ]; then
                                        echo "❌ Failed to push after ${MAX_RETRIES} attempts"
                                        return 1
                                    fi
                                    
                                    echo "Waiting ${DELAY} seconds before retry..."
                                    sleep ${DELAY}
                                fi
                            done
                        }
                        
                        push_with_retry "${DOCKER_IMAGE_NAME}" "${DOCKER_IMAGE_TAG}" || exit 1
                        push_with_retry "${DOCKER_IMAGE_NAME}" "latest" || exit 1
                        
                        docker logout
                        
                        echo "✅✅✅ DOCKER PUSH COMPLETED SUCCESSFULLY! ✅✅✅"
                    '''
                }
            }
            post {
                failure {
                    echo "❌❌❌ DOCKER BUILD OR PUSH FAILED AFTER MULTIPLE RETRIES ❌❌❌"
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
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, sonar-check.json', allowEmptyArchive: true
            
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json sonar-check.json || true
            '''
            
            echo "✅ Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "🐳 Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
            echo "📦 View on Docker Hub: https://hub.docker.com/r/${env.DOCKER_IMAGE_NAME}/tags"
            echo "📊 View on SonarCloud: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "📊 SonarCloud results: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
        }
    }
}