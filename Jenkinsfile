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
        DJANGO_SETTINGS_MODULE = 'myproject.settings'
        SECRET_KEY = sh(script: 'python3 -c "import secrets; print(secrets.token_urlsafe(50))"', returnStdout: true).trim()
        
        DOCKER_IMAGE_NAME = 'tasnimelleuchenis/django-contact-app'
        DOCKER_IMAGE_TAG = sh(script: '''#!/bin/bash
            date "+%Y-%m-%d-at-%H-%M-%S-build-${BUILD_NUMBER}" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g'
        ''', returnStdout: true).trim()
        
        // GitHub token for API access
        GITHUB_TOKEN = credentials('github-token')  // Your existing GitHub token
        GITHUB_OWNER = 'tassnimelleuch'
        GITHUB_REPO = 'django-contact-app'
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
                echo "✅ Workspace cleaned and code checked out"
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    sh '''
                        ${PYTHON} -m venv ${VENV_DIR}
                        ${PIP} install --upgrade pip setuptools wheel
                        ${PIP} install -r requirements.txt
                        
                        export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
                        export SECRET_KEY='${SECRET_KEY}'
                        
                        ${PYTEST} accounts \
                            --cov \
                            --cov-report=xml:coverage.xml \
                            --junitxml=junit-results.xml
                        
                        ${PYLINT} accounts \
                            --output-format=json:pylint-report.json \
                            --exit-zero
                    '''
                }
            }
        }
        
        // ===== THIS IS WHAT YOU WANT - JUST CHECK GITHUB STATUS =====
        stage('Check SonarCloud Status from GitHub') {
            steps {
                script {
                    echo "🔍 Checking SonarCloud status on GitHub..."
                    
                    // Get the current commit SHA
                    def commitSha = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    
                    // Maximum wait time (30 minutes)
                    int maxWait = 30
                    int waited = 0
                    
                    while (waited < maxWait) {
                        // Check GitHub commit statuses
                        def response = sh(
                            script: """
                                curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
                                "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits/${commitSha}/status"
                            """,
                            returnStdout: true
                        )
                        
                        // Parse the response for SonarCloud check
                        def sonarStatus = sh(
                            script: """
                                echo '${response}' | jq -r '.statuses[]? | select(.context | contains("sonar") or contains("SonarCloud") or contains("Code Analysis")) | .state' | head -1
                            """,
                            returnStdout: true
                        ).trim()
                        
                        def sonarUrl = sh(
                            script: """
                                echo '${response}' | jq -r '.statuses[]? | select(.context | contains("sonar") or contains("SonarCloud") or contains("Code Analysis")) | .target_url' | head -1
                            """,
                            returnStdout: true
                        ).trim()
                        
                        if (sonarStatus) {
                            echo "SonarCloud Status: ${sonarStatus}"
                            
                            if (sonarStatus == 'success') {
                                echo "✅✅✅ SONARCLOUD CHECK PASSED ON GITHUB! ✅✅✅"
                                echo "📊 View details: ${sonarUrl}"
                                break
                            } 
                            else if (sonarStatus == 'failure') {
                                echo "❌❌❌ SONARCLOUD CHECK FAILED ON GITHUB! ❌❌❌"
                                echo "📊 View details: ${sonarUrl}"
                                error "SonarCloud check failed on GitHub"
                            } 
                            else if (sonarStatus == 'pending') {
                                echo "⏳ SonarCloud still pending... (${waited} minutes)"
                            }
                        } else {
                            echo "⏳ Waiting for SonarCloud to post status... (${waited} minutes)"
                        }
                        
                        // Wait 1 minute before checking again
                        sleep time: 1, unit: 'MINUTES'
                        waited++
                    }
                    
                    if (waited >= maxWait) {
                        error "Timeout waiting for SonarCloud status on GitHub after ${maxWait} minutes"
                    }
                }
            }
        }
        
        stage('Docker Build and Push') {
            when {
                expression { fileExists('Dockerfile') }
            }
            environment {
                DOCKER_HUB_CREDS = credentials('docker-hub-credentials')
            }
            steps {
                script {
                    echo "🐳 Building and pushing Docker image..."
                    
                    sh """
                        docker build -t ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG} -t ${DOCKER_IMAGE_NAME}:latest .
                        echo "\$DOCKER_HUB_CREDS_PSW" | docker login -u "\$DOCKER_HUB_CREDS_USR" --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        docker push ${DOCKER_IMAGE_NAME}:latest
                        docker logout
                    """
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json', allowEmptyArchive: true
            sh 'rm -rf ${VENV_DIR} || true'
        }
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
        }
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
        }
    }
}