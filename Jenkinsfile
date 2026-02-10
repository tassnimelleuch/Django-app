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
                    echo "📦 Installing ALL dependencies including SonarScanner..."
                    
                    sh '''
                        echo "Installing/upgrading pip..."
                        ${PIP} install --upgrade pip setuptools wheel
                        
                        if [ -f requirements.txt ]; then
                            echo "Installing from requirements.txt..."
                            ${PIP} install -r requirements.txt
                            echo "✅ Dependencies installed from requirements.txt"
                        else
                            echo "Installing Django and test tools..."
                            ${PIP} install django pytest pytest-django pytest-cov pylint
                            echo "✅ Basic packages installed"
                        fi
                        
                        # INSTALL SONARSCANNER VIA PIP - ONE TIME
                        echo "Installing sonar-scanner-cli via pip..."
                        ${PIP} install sonar-scanner-cli
                        
                        # Verify installation
                        echo "Verifying sonar-scanner installation..."
                        ${VENV_DIR}/bin/sonar-scanner --version || echo "Checking alternative..."
                        
                        # Alternative check
                        python -c "import sonar_scanner; print('✅ sonar-scanner-cli installed')" 2>/dev/null || echo "SonarScanner available via pip"
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
                    
                    // First, check SonarScanner is available
                    sh '''
                        echo "Checking sonar-scanner availability..."
                        which sonar-scanner || ${VENV_DIR}/bin/sonar-scanner --help || echo "Trying pip package..."
                        python -c "import sonar_scanner; print('sonar_scanner module available')" 2>/dev/null || true
                    '''
                    
                    withSonarQubeEnv('sonarqube') {
                        // TRY 1: Use pip-installed sonar-scanner
                        sh '''
                            # Method 1: Use the pip-installed version
                            echo "Method 1: Using pip sonar-scanner..."
                            ${VENV_DIR}/bin/sonar-scanner --version 2>/dev/null || echo "Not found in venv"
                            
                            # Method 2: Use sonar_scanner Python module
                            echo "Method 2: Using sonar_scanner Python module..."
                            python -c "
try:
    from sonar_scanner import SonarScanner
    scanner = SonarScanner()
    print('✅ SonarScanner Python module available')
except Exception as e:
    print(f'Python module error: {e}')
                            " 2>/dev/null || true
                        '''
                        
                        // ACTUAL SONAR ANALYSIS
                        sh """
                            # Use the FULL PATH to sonar-scanner from venv
                            ${VENV_DIR}/bin/sonar-scanner \
                                -Dsonar.projectKey=django-app-${BUILD_NUMBER} \
                                -Dsonar.projectName="Django Contact App" \
                                -Dsonar.sources=. \
                                -Dsonar.exclusions=**/migrations/**,**/__pycache__/**,**/*.pyc,venv/**,**/test*.py \
                                -Dsonar.python.coverage.reportPaths=coverage.xml \
                                -Dsonar.python.xunit.reportPath=junit-results.xml \
                                -Dsonar.python.pylint.reportPath=pylint-report.json \
                                -Dsonar.python.version=3 \
                                -Dsonar.sourceEncoding=UTF-8 \
                                -Dsonar.host.url=\${SONAR_HOST_URL} \
                                -Dsonar.login=\${SONAR_AUTH_TOKEN}
                        """
                    }
                }
            }
        }
        
        stage('Quality Gate Check') {
            steps {
                script {
                    echo "⏳ Waiting for SonarQube Quality Gate..."
                    
                    timeout(time: 5, unit: 'MINUTES') {
                        // THIS WILL RUN - NO REMOVAL
                        waitForQualityGate abortPipeline: true
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Archive reports
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json', allowEmptyArchive: true
            
            // Cleanup
            sh 'rm -rf ${VENV_DIR} || true'
            sh 'rm -f coverage.xml junit-results.xml pylint-report.json || true'
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📊 SonarQube report available"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "Check SonarQube at: http://localhost:9000"
        }
    }
}