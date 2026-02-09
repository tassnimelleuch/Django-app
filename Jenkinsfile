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
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                script {
                    echo "Using Python: ${PYTHON}"
                    sh '''
                        ${PYTHON} --version
                        ${PYTHON} -m pip --version || echo "pip not available, will install in venv"
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
                        ${PIP} install --upgrade pip setuptools wheel
                        if [ -f requirements.txt ]; then
                            ${PIP} install -r requirements.txt
                        else
                            echo "requirements.txt not found, installing test dependencies"
                            ${PIP} install pytest pytest-cov pytest-html pylint pylint-django
                        fi
                    '''
                }
            }
        }
        
        stage('Code Quality & Tests') {
            parallel {
                stage('Static Analysis - PyLint') {
                    steps {
                        script {
                            sh '''
                                echo "Running PyLint analysis..."
                                ${PYLINT} accounts/ --load-plugins=pylint_django \
                                    --django-settings-module=myproject.settings \
                                    --output-format=json > pylint-report.json || true
                                
                                # Also generate a readable report
                                ${PYLINT} accounts/ --load-plugins=pylint_django \
                                    --django-settings-module=myproject.settings \
                                    --output-format=colorized > pylint-output.txt || true
                            '''
                        }
                    }
                    
                    post {
                        always {
                            archiveArtifacts artifacts: 'pylint-output.txt'
                        }
                    }
                }
                
                stage('Unit Tests - Pytest') {
                    steps {
                        script {
                            sh '''
                                echo "Running tests with Pytest..."
                                ${PYTEST} tests/ \
                                    --cov=accounts \
                                    --cov-report=xml:coverage.xml \
                                    --cov-report=html:htmlcov \
                                    --junitxml=junit.xml \
                                    --html=pytest-report.html \
                                    -v
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Generate Reports') {
            steps {
                script {
                    echo "Generating test and coverage reports..."
                    sh '''
                        # Create a summary report
                        echo "Test Execution Summary" > test-summary.txt
                        echo "=====================" >> test-summary.txt
                        date >> test-summary.txt
                        echo "" >> test-summary.txt
                        
                        # Extract test results if junit.xml exists
                        if [ -f junit.xml ]; then
                            echo "JUnit Report: junit.xml" >> test-summary.txt
                        fi
                        
                        if [ -f coverage.xml ]; then
                            echo "Coverage Report: coverage.xml" >> test-summary.txt
                        fi
                    '''
                }
            }
        }
    }
    
    post {
        always {
            junit 'junit.xml'
            
            publishHTML(target: [
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Test Coverage Report',
                keepAll: true
            ])
            
            publishHTML(target: [
                reportDir: '.',
                reportFiles: 'pytest-report.html',
                reportName: 'Pytest Detailed Report',
                keepAll: true
            ])
            
            archiveArtifacts artifacts: 'junit.xml, coverage.xml, pylint-report.json, test-summary.txt'
            
            sh 'rm -rf ${VENV_DIR} || true'
        }
        
        success {
            script {
                echo "Pipeline succeeded! ✅"
                echo "Test results available in Jenkins UI"
                echo "Coverage report: ${BUILD_URL}Coverage_20Report/"
                echo "Detailed pytest report: ${BUILD_URL}Pytest_20Detailed_20Report/"
            }
        }
        
        unstable {
            script {
                echo "Pipeline completed with test failures! ⚠️"
                echo "Check the 'Test Results' tab for details"
            }
        }
        
        failure {
            script {
                echo "Pipeline failed! ❌"
                echo "Check the console output for errors"
                
             
            }
        }
        
        cleanup {
            script {
                echo "Cleaning up workspace..."
                sh 'find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true'
                sh 'find . -name "*.pyc" -delete 2>/dev/null || true'
            }
        }
    }
}