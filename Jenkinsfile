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
        
        stage('Check/Install SonarScanner') {
            steps {
                script {
                    echo "🔧 Checking SonarScanner installation..."
                    
                    sh '''
                        # Check if sonar-scanner is already installed
                        if command -v sonar-scanner &> /dev/null; then
                            echo "✅ SonarScanner already installed globally"
                            sonar-scanner --version
                        else
                            echo "📦 Installing SonarScanner globally..."
                            
                            # Method 1: Install from official binaries
                            wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
                            unzip -q sonar-scanner-cli-*.zip
                            rm sonar-scanner-cli-*.zip
                            
                            # Add to PATH for current session
                            export SONAR_SCANNER_HOME=$(pwd)/sonar-scanner-5.0.1.3006-linux
                            export PATH=$PATH:$SONAR_SCANNER_HOME/bin
                            
                            # Test it
                            $SONAR_SCANNER_HOME/bin/sonar-scanner --version
                            echo "✅ SonarScanner installed in workspace"
                        fi
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
                    echo "📦 Installing Python dependencies..."
                    
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
                    
                    // Find sonar-scanner path
                    sh '''
                        # Find sonar-scanner
                        if command -v sonar-scanner &> /dev/null; then
                            echo "Using global sonar-scanner"
                            SONAR_SCANNER_CMD="sonar-scanner"
                        elif [ -d "sonar-scanner-5.0.1.3006-linux" ]; then
                            echo "Using workspace sonar-scanner"
                            SONAR_SCANNER_CMD="$(pwd)/sonar-scanner-5.0.1.3006-linux/bin/sonar-scanner"
                        else
                            echo "ERROR: sonar-scanner not found!"
                            exit 1
                        fi
                        echo "SonarScanner command: $SONAR_SCANNER_CMD"
                    '''
                    
                    withSonarQubeEnv('sonarqube') {
                        sh '''
                            # Determine which sonar-scanner to use
                            if command -v sonar-scanner &> /dev/null; then
                                SCANNER="sonar-scanner"
                            elif [ -d "sonar-scanner-5.0.1.3006-linux" ]; then
                                SCANNER="$(pwd)/sonar-scanner-5.0.1.3006-linux/bin/sonar-scanner"
                            else
                                echo "ERROR: No sonar-scanner found!"
                                exit 1
                            fi
                            
                            $SCANNER \
                                -Dsonar.projectKey=django-app-${BUILD_NUMBER} \
                                -Dsonar.projectName="Django Contact App #${BUILD_NUMBER}" \
                                -Dsonar.sources=. \
                                -Dsonar.exclusions=**/migrations/**,**/__pycache__/**,**/*.pyc,venv/**,**/test*.py \
                                -Dsonar.python.coverage.reportPaths=coverage.xml \
                                -Dsonar.python.xunit.reportPath=junit-results.xml \
                                -Dsonar.python.pylint.reportPath=pylint-report.json \
                                -Dsonar.python.version=3 \
                                -Dsonar.sourceEncoding=UTF-8
                        '''
                    }
                }
            }
        }
        
        stage('Quality Gate Check') {
            steps {
                script {
                    echo "⏳ Waiting for SonarQube Quality Gate..."
                    
                    timeout(time: 5, unit: 'MINUTES') {
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
            
            // Cleanup - keep sonar-scanner for next runs
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json || true
                # Keep sonar-scanner directory for future runs
            '''
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📊 SonarQube report: http://localhost:9000/dashboard?id=django-app-${BUILD_NUMBER}"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
        }
    }
}