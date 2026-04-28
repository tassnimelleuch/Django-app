pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')  
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
        
        // ===== AZURE AKS CONFIGURATION =====
        AZURE_RESOURCE_GROUP = 'aks-deployment'    
        AKS_CLUSTER_NAME = 'django-app'                   
        K8S_NAMESPACE = 'default'
        K8S_DEPLOYMENT = 'django-contact-app'
        K8S_SERVICE = 'django-contact-service'
    }
    
    stages {
        stage('Force Fail') {
            steps {
                sh 'exit 1'
            }
        }
        stage('Clean Workspace') {
            steps {
                sh '''
                    rm -rf venv || true
                    rm -f coverage.xml junit-results.xml sonar-check.json || true
                    rm -f init_django.py check-sonarcloud.sh full-response.json sonarcloud-status.txt || true
                    echo "✅ Workspace cleaned (build tts removed)"
                '''
                script {
                    echo " Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
                    echo "🐳 Docker tag: ${DOCKER_IMAGE_TAG}"
                    echo "🔍 Commit: ${GIT_COMMIT}"
                }
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    echo 'Creating virtual environment...'
                    sh '${PYTHON} -m venv ${VENV_DIR}'

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

MAX_ATTEMPTS=12
SLEEP_SECONDS=15

for attempt in $(seq 1 ${MAX_ATTEMPTS}); do
    echo "Fetching check runs from GitHub API... (attempt ${attempt}/${MAX_ATTEMPTS})"
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/commits/${GIT_COMMIT}/check-runs" > full-response.json

    if grep -i "sonarcloud" full-response.json > /dev/null; then
        echo "✅ SonarCloud check found"
        break
    fi

    if [ $attempt -lt ${MAX_ATTEMPTS} ]; then
        echo "⏳ SonarCloud check not found yet. Waiting ${SLEEP_SECONDS}s..."
        sleep ${SLEEP_SECONDS}
    fi
done

echo "===== FULL GITHUB RESPONSE ====="
cat full-response.json
echo "===== END RESPONSE ====="

if grep -i "sonarcloud" full-response.json > /dev/null; then
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
            echo "QUALITY GATE FAILED!"
            exit 1
            ;;
        *)
            echo "⚠️ SonarCloud status: $CONCLUSION"
            ;;
    esac
else
    echo "SONARCLOUD NOT FOUND IN GITHUB API AFTER WAITING"
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
        
        stage('Docker Image Build') {
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

                }
            }
        }

            stage('Push Docker Image') {
                environment {
                    DOCKER_HUB_CREDS = credentials('docker-hub-credentials')
                }
                steps {
                    script {
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
                    echo "Docker build and push completed successfully"
                }
            }
        }
        
        // ===================================================================
        // MINIKUBE DEPLOYMENT STAGES
        // ===================================================================
        /*
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
                        
                        echo "⏳ Waiting for old pods to terminate..."
                        sleep 10
                        
                        echo "🔍 Looking for the newest running pod..."
                        POD_NAME=$(kubectl get pods -l app=django-contact-app \
                            --field-selector=status.phase=Running \
                            --sort-by=.metadata.creationTimestamp \
                            -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null)
                        
                        if [ -z "$POD_NAME" ]; then
                            echo "⚠️ No running pod found with field selector, trying all pods..."
                            POD_NAME=$(kubectl get pods -l app=django-contact-app \
                                --sort-by=.metadata.creationTimestamp \
                                -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null)
                        fi
                        
                        if [ -z "$POD_NAME" ]; then
                            echo "❌ No pod found!"
                            kubectl get pods -l app=django-contact-app
                            exit 1
                        fi
                        
                        echo "📦 Latest pod: $POD_NAME"
                        
                        POD_STATUS=$(kubectl get pod $POD_NAME -o jsonpath='{.status.phase}')
                        echo "📊 Pod status: $POD_STATUS"
                        
                        echo "⏳ Waiting for pod to be ready (this may take a moment)..."
                        if kubectl wait --for=condition=ready pod/$POD_NAME --timeout=120s; then
                            echo "✅ Pod is ready!"
                        else
                            echo "❌ Pod failed to become ready within timeout"
                            echo "📋 Pod details:"
                            kubectl describe pod $POD_NAME
                            echo "📋 Init container logs (fix-permissions):"
                            kubectl logs $POD_NAME -c fix-permissions 2>/dev/null || echo "No fix-permissions logs"
                            echo "📋 Init container logs (migrate):"
                            kubectl logs $POD_NAME -c migrate 2>/dev/null || echo "No migrate logs"
                            echo "📋 Recent events:"
                            kubectl get events --field-selector involvedObject.name=$POD_NAME --all-namespaces 2>/dev/null | tail -10 || echo "No events"
                            exit 1
                        fi
                        
                        echo "📋 Recent logs from main container:"
                        kubectl logs $POD_NAME --tail=20 2>/dev/null || echo "No logs available"
                        
                        echo "🌐 Getting service URL..."
                        MINIKUBE_URL=$(minikube service django-contact-service --url 2>/dev/null || echo "")
                        
                        if [ -n "$MINIKUBE_URL" ]; then
                            echo "✅ Application is accessible at: $MINIKUBE_URL"
                            
                            echo "🔍 Testing application endpoint..."
                            sleep 5
                            
                            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 $MINIKUBE_URL || echo "Failed")
                            
                            if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "301" ]; then
                                echo "✅ Application responded with HTTP $HTTP_CODE"
                            else
                                echo "⚠️ Application returned HTTP $HTTP_CODE - may need investigation"
                            fi
                            
                            echo "🔗 Try accessing: $MINIKUBE_URL"
                        else
                            echo "⚠️ Could not get Minikube URL"
                            echo "🔄 Attempting port-forward as alternative..."
                            kubectl port-forward pod/$POD_NAME 8000:8000 --timeout=5s &
                            PF_PID=$!
                            sleep 3
                            curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 || echo "Port-forward test failed"
                            kill $PF_PID 2>/dev/null || true
                        fi
                        
                        echo "✅ Verification complete"
                    '''
                }
            }
        }

        // BUG FIX: This stage was placed OUTSIDE the stages{} block in the original.
        // It must be the last stage inside stages{} to run on pipeline failure.
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
        } */
        
        // ===================================================================
        // AZURE AKS DEPLOYMENT STAGES 
        // ===================================================================
        

        
        stage('Prepare and Deploy to AKS') {
            steps {
                script {
                    echo "📝 Preparing Kubernetes manifests for AKS..."
                    
                    // Update image tag in deployment
                    sh """
                        sed -i 's|image: tasnimelleuchenis/django-contact-app:.*|image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}|g' k8s/deployment.yaml
                        echo "✅ Updated deployment with new image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                    """
                    
                    // Show the updated image
                    sh "grep -A1 'image:' k8s/deployment.yaml | head -2"

                    echo "🚀 Deploying to Azure Kubernetes Service..."
                    
                    sh '''
                        # Function to apply with retry
                        apply_with_retry() {
                            local file=$1
                            local name=$2
                            local max_retries=3
                            local retry=0
                            
                            echo "📄 Applying $name from $file..."
                            
                            while [ $retry -lt $max_retries ]; do
                                if kubectl apply -f $file --namespace ${K8S_NAMESPACE}; then
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
                            
                            echo "Failed to apply $name after $max_retries attempts"
                            return 1
                        }
                        
                        # Create namespace if it doesn't exist
                        kubectl create namespace ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                        
                        # Apply secrets first (if they exist)
                        if [ -f k8s/secret.yaml ]; then
                            echo "Applying secrets"
                            kubectl apply -f k8s/secret.yaml --namespace ${K8S_NAMESPACE}
                        fi
                        
                        # Apply PVC (persistent storage)
                        echo " Applying PVC (10Mi)..."
                        if [ -f k8s/pvc.yaml ]; then
                            apply_with_retry "k8s/pvc.yaml" "PVC" || exit 1
                        else
                            echo " PVC file not found, skipping..."
                        fi
                        
                        # Apply deployment
                        echo "Applying deployment with image: ${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}"
                        apply_with_retry "k8s/deployment.yaml" "Deployment" || exit 1
                        
                        # Apply service (NodePort - free!)
                        echo "Applying service (NodePort - no extra cost)..."
                        if [ -f k8s/service.yaml ]; then
                            apply_with_retry "k8s/service.yaml" "Service" || exit 1
                        else
                            echo "⚠️ Service file not found, skipping..."
                        fi
                        
                        echo "✅ All Kubernetes resources applied successfully"
                        
                        # Show current resources
                        echo "📊 Current pods:"
                        kubectl get pods -n ${K8S_NAMESPACE} -l app=django-contact-app
                        
                        echo "Current services:"
                        kubectl get services -n ${K8S_NAMESPACE}
                    '''
                }
            }
        }

        stage('Wait for AKS Rollout and Verify') {
            steps {
                script {
                    echo "⏳ Waiting for AKS deployment to be ready"
                    
                    sh '''
                        # Show pod status during wait
                        kubectl get pods -n ${K8S_NAMESPACE} -l app=django-contact-app -w &
                        WATCH_PID=$!
                        
                        echo "Waiting for rollout to complete..."
                        if kubectl rollout status deployment/${K8S_DEPLOYMENT} --namespace ${K8S_NAMESPACE} --timeout=300s; then
                            kill $WATCH_PID 2>/dev/null || true
                            echo "✅ Deployment rollout successful"
                        else
                            kill $WATCH_PID 2>/dev/null || true
                            echo "❌ Deployment rollout failed"
                            
                            # Debug information
                            POD_NAME=$(kubectl get pods -n ${K8S_NAMESPACE} -l app=django-contact-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
                            if [ -n "$POD_NAME" ]; then
                                echo "📋 Pod events:"
                                kubectl describe pod $POD_NAME -n ${K8S_NAMESPACE} | grep -A 20 Events
                                echo "📋 Init container logs:"
                                kubectl logs $POD_NAME -c fix-permissions -n ${K8S_NAMESPACE} 2>/dev/null || echo "No fix-permissions logs"
                                kubectl logs $POD_NAME -c migrate -n ${K8S_NAMESPACE} 2>/dev/null || echo "No migrate logs"
                            fi
                            exit 1
                        fi
                    '''

                    echo "🔍 Verifying AKS deployment..."
                    
                    sh '''
                        # Wait for old pods to terminate first
                        sleep 10
                        
                        # Get the NEWEST running pod (sorted by creation time)
                        POD_NAME=$(kubectl get pods -n default \
                            -l app=django-contact-app \
                            --sort-by=.metadata.creationTimestamp \
                            -o jsonpath='{.items[-1].metadata.name}')
                        
                        if [ -z "$POD_NAME" ]; then
                            echo "❌ No pod found!"
                            exit 1
                        fi
                        
                        echo "📦📦 Latest pod: $POD_NAME"
                        
                        # Wait until it's actually Running (up to 120s)
                        echo "⏳ Waiting for pod to reach Running state..."
                        for i in $(seq 1 24); do
                            POD_STATUS=$(kubectl get pod $POD_NAME -n default -o jsonpath='{.status.phase}')
                            echo "   Attempt $i/24 - Status: $POD_STATUS"
                            
                            if [ "$POD_STATUS" = "Running" ]; then
                                echo "✅ Pod is Running!"
                                break
                            fi
                            
                            if [ $i -eq 24 ]; then
                                echo "❌ Pod never reached Running state!"
                                kubectl describe pod $POD_NAME -n default
                                exit 1
                            fi
                            
                            sleep 5
                        done
                        
                        # Show recent logs
                        echo "📋 Recent logs:"
                        kubectl logs $POD_NAME -n default --tail=20
                    '''
                }
            }
        }
        stage('Restart Port Forward') {
            steps {
                script {
                    echo "🔄 Restarting port-forward service..."
                    sh '''
                        sudo systemctl restart kubectl-port-forward
                        sleep 5
                        
                        if systemctl is-active --quiet kubectl-port-forward; then
                            echo " Port-forward service is running"
                        else
                            echo "❌ Port-forward service failed to start!"
                            sudo journalctl -u kubectl-port-forward --no-pager -n 20
                            exit 1
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
                        echo "Undoing deployment..."
                        kubectl rollout undo deployment/${K8S_DEPLOYMENT} --namespace ${K8S_NAMESPACE}
                        
                        echo "Waiting for rollback..."
                        kubectl rollout status deployment/${K8S_DEPLOYMENT} --namespace ${K8S_NAMESPACE} --timeout=60s
                        
                        echo "✅ Rollback completed"
                        
                        # Show current pods after rollback
                        kubectl get pods -n ${K8S_NAMESPACE} -l app=django-contact-app
                    '''
                    
                    echo "✅ Rollback finished"
                }
            }
        }

    } 

    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, sonar-check.json, pylint-report.json', allowEmptyArchive: true
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml  sonar-check.json init_django.py check-sonarcloud.sh full-response.json sonarcloud-status.txt || true
            '''
            echo "✅ Pipeline execution completed"
        }

        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "🐳 Docker image: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"

            script {
                def VM_PUBLIC_IP = "51.103.56.25"

                def NODE_PORT = sh(
                    script: "kubectl get service ${K8S_SERVICE} -n ${K8S_NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo '30000'",
                    returnStdout: true
                ).trim()

                echo "🌐🌐🌐 ACCESS YOUR APP HERE: http://${VM_PUBLIC_IP}:8000 🌐🌐🌐"
                echo ""
                echo "📱 Quick Access Links:"
                echo "   • Via port-forward (FASTEST): http://${VM_PUBLIC_IP}:8000"
                echo "   • Via NodePort (if port-forward fails): http://${VM_PUBLIC_IP}:${NODE_PORT}"
                echo ""
                echo "🔍 Debug Commands (run on VM):"
                echo "   • Check port-forward: ps aux | grep port-forward"
                echo "   • View logs: cat port-forward.log"
                echo "   • Restart manually: kubectl port-forward --address 0.0.0.0 service/${K8S_SERVICE} 8000:8000 -n ${K8S_NAMESPACE}"
                echo ""
                echo "📊 View on Docker Hub: https://hub.docker.com/r/${env.DOCKER_IMAGE_NAME}/tags"
                echo "📊 View on SonarCloud: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"
            }
        }

        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "📅 Build: ${HUMAN_READABLE_DATE} (#${BUILD_NUMBER})"
            echo "📊 SonarCloud results: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}"

            script {
                def COMMITTER_EMAIL = sh(
                    script: "git log -1 --pretty=format:'%ae'",
                    returnStdout: true
                ).trim()

                def TRIGGERED_BY = currentBuild.getBuildCauses('hudson.model.UserIdCause')

                def recipient
                if (TRIGGERED_BY) {
                    wrap([$class: 'BuildUser']) {
                        recipient = env.BUILD_USER_EMAIL
                    }
                } else {
                    recipient = COMMITTER_EMAIL
                }

                emailext(
                    to: "${recipient}",
                    subject: "❌ Jenkins FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                    body: """
    Build failed.

    Job: ${env.JOB_NAME}
    Build number: ${env.BUILD_NUMBER}
    Build URL: ${env.BUILD_URL}
    Date: ${HUMAN_READABLE_DATE}
    Commit: ${GIT_COMMIT}
    SonarCloud: https://sonarcloud.io/dashboard?id=${SONAR_PROJECT_KEY}
    """
                )
            }
        }

        fixed {
            script {
                def COMMITTER_EMAIL = sh(
                    script: "git log -1 --pretty=format:'%ae'",
                    returnStdout: true
                ).trim()

                def TRIGGERED_BY = currentBuild.getBuildCauses('hudson.model.UserIdCause')

                def recipient
                if (TRIGGERED_BY) {
                    wrap([$class: 'BuildUser']) {
                        recipient = env.BUILD_USER_EMAIL
                    }
                } else {
                    recipient = COMMITTER_EMAIL
                }

                emailext(
                    to: "${recipient}",
                    subject: "✅ Jenkins FIXED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                    body: """
    The pipeline is successful again after previous failure(s).

    Job: ${env.JOB_NAME}
    Build number: ${env.BUILD_NUMBER}
    Build URL: ${env.BUILD_URL}
    Date: ${HUMAN_READABLE_DATE}
    """
                )
            }
        }
    }
}