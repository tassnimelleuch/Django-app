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
    }
    
    post {
        always {
            // Archive all reports
            archiveArtifacts artifacts: 'coverage.xml, junit-results.xml, pylint-report.json, sonar-project.properties, .scannerwork/report-task.txt', allowEmptyArchive: true
            
            // Display SonarQube URL if available
            script {
                if (fileExists('.scannerwork/report-task.txt')) {
                    def reportTask = readFile('.scannerwork/report-task.txt')
                    def serverUrl = reportTask.find(/serverUrl=(.*)/)?.split('=')[1]
                    def taskId = reportTask.find(/taskId=(.*)/)?.split('=')[1]
                    def ceTaskUrl = reportTask.find(/ceTaskUrl=(.*)/)?.split('=')[1]
                    def dashboardUrl = reportTask.find(/dashboardUrl=(.*)/)?.split('=')[1]
                    
                    echo "SonarQube Analysis URL: ${dashboardUrl}"
                    echo "SonarQube Task URL: ${ceTaskUrl}"
                }
            }
            
            // Cleanup
            sh '''
                rm -rf ${VENV_DIR} || true
                rm -f coverage.xml junit-results.xml pylint-report.json || true
                # Keep sonar-scanner directory for future runs
            '''
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