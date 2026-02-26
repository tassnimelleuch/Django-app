pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')  // Increased timeout for image pulls
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
        
        K8S_NAMESPACE = 'default'
        K8S_DEPLOYMENT = 'django-contact-app'
        K8S_SERVICE = 'django-contact-service'
        
        // Minikube environment for Jenkins
        MINIKUBE_HOME = '/var/lib/jenkins'
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                sh '''
                    rm -rf venv || true
                    rm -f coverage.xml junit-results.xml pylint-report.json sonar-check.json || true
                    rm -f init_django.py check-sonarcloud.sh full-response.json sonarcloud-status.txt || true
                    echo "✅ Workspace cleaned (build artifacts removed)"
                '''
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
                        
                        writeFile file: 'check-sonarcloud.sh', text: '''#!/bin/bash
set -e

echo "Fetching check runs from GitHub API..."
curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits/${GIT_COMMIT}/check-runs" > full-response.json

echo "===== FULL GITHUB RESPONSE ====="
cat full-response.json
echo "===== END RESPONSE ====="

if grep -i "sonarcloud" full-response.json > /dev/null; then
    echo "✅ SonarCloud check found"
    
    CONCLUSION=$(grep -i -A5 "sonarcloud" full-response.json | \
                grep -i "conclusion" | \
                head -1 | \
                cut -d':' -f2 | \
                tr -d ' ,"')
    
    echo "SONARCLOUD_CONCLUSION=$CONCLUSION" > sonarcloud-status.txt
    
    case "$CONCLUSION" in
        "success")
            echo "✅✅✅ QUALITY GATE PASSED! ✅✅✅"
            ;;
        "failure")
            echo "QUALITY GATE FAILED! "
            exit 1
            ;;
        *)
            echo "⚠️ SonarCloud status: $CONCLUSION"
            ;;
    esac
else
    echo "SONARCLOUD NOT FOUND IN GITHUB API!"
    echo "First 20 lines of response:"
    head -20 full-response.json
    exit 1
fi
'''
                        
                        sh 'chmod +x check-sonarcloud.sh'
                        
                        withEnv([
                            "GITHUB_OWNER=${GITHUB_OWNER}",
                            "GITHUB_REPO=${GITHUB_REPO}",
                            "GIT_COMMIT=${GIT_COMMIT}"
                        ]) {
                            sh './check-sonarcloud.sh'
                        }
                        
                        if (fileExists('sonarcloud-status.txt')) {
                            def conclusion = readFile('sonarcloud-status.txt').trim()
                            echo "SonarCloud conclusion from file: ${conclusion}"
                        }
                        
                        sh 'rm -f check-sonarcloud.sh'
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
        
        // ============= FIXED MINIKUBE CD STAGES =============

        stage('Setup Minikube Access') {
            steps {
                script {
                    sh '''
                        export MINIKUBE_HOME=/var/lib/jenkins
                        export KUBECONFIG=/var/lib/jenkins/.kube/config
                        
                        echo "🔧 Verifying Minikube access..."
                        minikube status || {
                            echo "❌ Minikube not running"
                            exit 1
                        }
                        
                        kubectl get nodes || {
                            echo "❌ Cannot access cluster"
                            exit 1
                        }
                        
                        echo "✅ Minikube ready!"
                    '''
                }
            }
        }
        
        stage('Deploy to Minikube') {
            when {
                expression { fileExists('k8s/deployment.yaml') }
                expression { fileExists('k8s/service.yaml') }
                expression { fileExists('k8s/pvc.yaml') }
            }
            steps {
                script {
                    echo "🚀 Deploying to Minikube..."
                    
                    sh """
                        sed -i 's|image: .*django-contact-app:.*|image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g' k8s/deployment.yaml
                        echo "✅ Updated deployment with new image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    """
                    
                    sh '''
                        export KUBECONFIG=/var/lib/jenkins/.kube/config
                        
                        # Function to apply with retry
                        apply_with_retry() {
                            local file=$1
                            local name=$2
                            local max_retries=3
                            local retry=0
                            
                            echo "📄 Applying $name from $file..."
                            
                            while [ $retry -lt $max_retries ]; do
                                if kubectl apply -f $file; then
                                    echo "✅ $name applied successfully"
                                    return 0
                                else
                                    retry=$((retry+1))
                                    if [ $retry -lt $max_retries ]; then
                                        echo "⚠️ Attempt $retry failed, retrying in 5 seconds..."
                                        sleep 5
                                    fi
                                fi
                            done
                            
                            echo "❌ Failed to apply $name after $max_retries attempts"
                            return 1
                        }
                        
                        echo "Applying Kubernetes resources..."
                        apply_with_retry "k8s/pvc.yaml" "PVC" || exit 1
                        apply_with_retry "k8s/deployment.yaml" "Deployment" || exit 1
                        apply_with_retry "k8s/service.yaml" "Service" || exit 1
                        
                        echo "✅ All Kubernetes resources applied successfully"
                    '''
                    
                    echo "✅ Deployment stage completed"
                }
            }
        }

        stage('Wait for Rollout') {
            steps {
                script {
                    echo "⏳ Waiting for deployment to be ready (this may take 3-5 minutes for first pull)..."
                    
                    sh '''
                        export KUBECONFIG=/var/lib/jenkins/.kube/config
                        
                        # Show pod status during wait
                        kubectl get pods -w &
                        WATCH_PID=$!
                        
                        echo "Waiting for rollout to complete..."
                        if kubectl rollout status deployment/django-contact-app --timeout=300s; then
                            kill $WATCH_PID 2>/dev/null || true
                            echo "✅ Deployment rollout successful"
                        else
                            kill $WATCH_PID 2>/dev/null || true
                            echo "❌ Deployment rollout failed"
                            echo "📋 Debug information:"
                            POD_NAME=$(kubectl get pods -l app=django-contact-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
                            if [ -n "$POD_NAME" ]; then
                                echo "Pod events:"
                                kubectl describe pod $POD_NAME | grep -A 20 Events
                                echo "Init container logs:"
                                kubectl logs $POD_NAME -c fix-permissions 2>/dev/null || true
                                kubectl logs $POD_NAME -c migrate 2>/dev/null || true
                            fi
                            exit 1
                        fi
                        
                        echo "📊 Current pods:"
                        kubectl get pods -l app=django-contact-app
                        
                        echo "📊 Current services:"
                        kubectl get services
                    '''
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                script {
                    echo "🔍 Verifying deployment..."
                    
                    sh '''
                        export KUBECONFIG=/var/lib/jenkins/.kube/config
                        
                        # Get pod name
                        POD_NAME=$(kubectl get pods -l app=django-contact-app -o jsonpath='{.items[0].metadata.name}')
                        echo "📦 Pod: $POD_NAME"
                        
                        # Wait for pod to be fully ready
                        echo "Waiting for pod to be ready..."
                        kubectl wait --for=condition=ready pod/$POD_NAME --timeout=60s || {
                            echo "❌ Pod not ready"
                            kubectl describe pod $POD_NAME
                            exit 1
                        }
                        
                        # Check pod status
                        POD_STATUS=$(kubectl get pod $POD_NAME -o jsonpath='{.status.phase}')
                        echo "📊 Pod status: $POD_STATUS"
                        
                        if [ "$POD_STATUS" = "Running" ]; then
                            echo "✅ Pod is running"
                            
                            # Check initContainers logs
                            echo "📋 fix-permissions logs:"
                            kubectl logs $POD_NAME -c fix-permissions 2>/dev/null || echo "No fix-permissions logs"
                            
                            echo "📋 migrate logs:"
                            kubectl logs $POD_NAME -c migrate 2>/dev/null || echo "No migrate logs"
                            
                            echo "📋 Main container logs:"
                            kubectl logs $POD_NAME --tail=20 2>/dev/null || echo "No main container logs"
                        else
                            echo "❌ Pod is not running! Status: $POD_STATUS"
                            kubectl describe pod $POD_NAME
                            exit 1
                        fi
                        
                        # Get service URL using minikube
                        echo "🌐 Getting service URL..."
                        MINIKUBE_URL=$(minikube service django-contact-service --url 2>/dev/null || echo "")
                        if [ -n "$MINIKUBE_URL" ]; then
                            echo "✅ Application is accessible at: $MINIKUBE_URL"
                            
                            # Test the endpoint
                            echo "Testing application endpoint..."
                            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $MINIKUBE_URL || echo "Failed")
                            echo "HTTP Status: $HTTP_CODE"
                        else
                            echo "⚠️ Could not get Minikube URL"
                        fi
                    '''
                }
            }
        }

        stage('Rollback on Failure') {
            when {
                expression { currentBuild.result == 'FAILURE' }
            }
            steps {
                script {
                    echo "⚠️ Deployment failed! Rolling back to previous version..."
                    
                    sh '''
                        export KUBECONFIG=/var/lib/jenkins/.kube/config
                        
                        echo "Undoing deployment..."
                        kubectl rollout undo deployment/django-contact-app
                        
                        echo "Waiting for rollback..."
                        kubectl rollout status deployment/django-contact-app --timeout=60s
                        
                        echo "✅ Rollback completed"
                    '''
                    
                    echo "✅ Rollback finished"
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, sonar-check.json', allowEmptyArchive: true
            
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json sonar-check.json init_django.py check-sonarcloud.sh full-response.json sonarcloud-status.txt || true
            '''
            
            echo "✅ Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "🐳 Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
            echo "📦 View on Docker Hub: https://hub.docker.com/r/${env.DOCKER_IMAGE_NAME}/tags"
            echo "📊 View on SonarCloud: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
            
            script {
                def SERVICE_URL = sh(
                    script: "minikube service ${K8S_SERVICE} --url || echo 'Service not available'",
                    returnStdout: true
                ).trim()
                echo "🌐 Access your app at: ${SERVICE_URL}"
            }
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "📊 SonarCloud results: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
        }
    }
}