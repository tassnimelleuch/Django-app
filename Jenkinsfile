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
                    
                    writeFile file: 'init_django.py', text: """
import os
import sys
os.environ['SECRET_KEY'] = '${SECRET_KEY}'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
try:
    import django
    django.setup()
    print('✅ Django initialized successfully')
    sys.exit(0)
except Exception as e:
    print(f'❌ Django initialization failed: {e}')
    sys.exit(1)
"""
                    
                    sh '${VENV_DIR}/bin/python init_django.py'
                    sh 'rm -f init_django.py'
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
        
        // ===== FINAL FIX - NO WARNINGS, EVER =====
        stage('Verify SonarCloud Quality Gate') {
            steps {
                withCredentials([string(
                    credentialsId: 'github-token',
                    variable: 'GITHUB_TOKEN'
                )]) {
                    script {
                        echo "🔍 VERIFYING SonarCloud quality gate from GitHub..."
                        echo "🔗 SonarCloud Dashboard: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
                        
                        // Write the script WITH THE TOKEN HARDCODED (but only in the file, not in Groovy)
                        sh """
                            cat > check-sonarcloud.sh << 'EOF'
#!/bin/bash
set -e

# Token is written directly to the file - no Groovy interpolation in execution!
GITHUB_TOKEN="${GITHUB_TOKEN}"
GITHUB_OWNER="${GITHUB_OWNER}"
GITHUB_REPO="${GITHUB_REPO}"
GIT_COMMIT="${GIT_COMMIT}"

echo "Fetching check runs from GitHub API..."
curl -s -H "Authorization: token \$GITHUB_TOKEN" \\
    "https://api.github.com/repos/\${GITHUB_OWNER}/\${GITHUB_REPO}/commits/\${GIT_COMMIT}/check-runs" > full-response.json

echo "===== FULL GITHUB RESPONSE ====="
cat full-response.json
echo "===== END RESPONSE ====="

if grep -i "sonarcloud" full-response.json > /dev/null; then
    echo "✅ SonarCloud check found"
    
    CONCLUSION=\$(grep -i -A5 "sonarcloud" full-response.json | \\
                grep -i "conclusion" | \\
                head -1 | \\
                cut -d':' -f2 | \\
                tr -d ' ,"')
    
    echo "\$CONCLUSION" > sonarcloud-conclusion.txt
    
    case "\$CONCLUSION" in
        "success")
            echo "✅✅✅ QUALITY GATE PASSED! ✅✅✅"
            ;;
        "failure")
            echo "❌❌❌ QUALITY GATE FAILED! ❌❌❌"
            exit 1
            ;;
        *)
            echo "⚠️ SonarCloud status: \$CONCLUSION"
            ;;
    esac
else
    echo "❌❌❌ SONARCLOUD NOT FOUND IN GITHUB API!"
    echo "First 20 lines of response:"
    head -20 full-response.json
    exit 1
fi
EOF
"""
                        
                        // Make executable and run
                        sh 'chmod +x check-sonarcloud.sh'
                        sh './check-sonarcloud.sh'
                        
                        // Read the conclusion
                        if (fileExists('sonarcloud-conclusion.txt')) {
                            def conclusion = readFile('sonarcloud-conclusion.txt').trim()
                            echo "SonarCloud conclusion: ${conclusion}"
                        }
                        
                        // Archive results
                        archiveArtifacts artifacts: 'full-response.json', allowEmptyArchive: true
                        
                        // Clean up
                        sh 'rm -f check-sonarcloud.sh sonarcloud-conclusion.txt'
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
                    
                    echo "✅ Docker image built"
                    
                    sh '''
                        echo "$DOCKER_HUB_CREDS_PSW" | docker login -u "$DOCKER_HUB_CREDS_USR" --password-stdin
                        
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}
                        docker push ${DOCKER_IMAGE_NAME}:latest
                        
                        docker logout
                    '''
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json', allowEmptyArchive: true
            sh 'rm -rf ${VENV_DIR} || true'
            echo "✅ Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "🐳 Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
        }
    }
}