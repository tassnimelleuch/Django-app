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
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
                echo "✅ Workspace cleaned and code checked out"
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
                    echo "🔧 Initializing Django..."
                    sh '''
                        ${VENV_DIR}/bin/python -c "
import os
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
                        DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
                        ${PYTEST} accounts \
                            --cov \
                            --cov-report=term \
                            --ds=myproject.settings \
                            --tb=short  # Shorter traceback for cleaner output
                    """
                }
            }
        }
        
        stage('Pylint Code Analysis') {
            steps {
                script {
                    echo "🔍 Running Pylint..."
                    sh """
                        ${PYLINT} accounts --fail-under=${PYLINT_THRESHOLD} || echo "⚠️ Pylint score below threshold, continuing..."
                    """
                }
            }
        }
    }
    
    post {
        always {
            // Cleanup
            sh 'rm -rf ${VENV_DIR} || true'
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
        }
    }
}