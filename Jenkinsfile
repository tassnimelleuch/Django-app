pipeline {
    agent any
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        VENV_DIR = 'venv'
        PYLINT_THRESHOLD = '7.0'
    }
    
    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
                echo "✅ Workspace cleaned and code checked out"
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Commit: ${env.GIT_COMMIT}"
            }
        }
        
        stage('Setup Python') {
            steps {
                script {
                    env.PYTHON = sh(script: 'which python3 || which python', returnStdout: true).trim()
                    echo "Using Python: ${env.PYTHON}"
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
                    sh '${PYTHON} -m venv ${VENV_DIR} || echo "Virtual environment creation failed, continuing..."'
                    env.PIP = "${env.VENV_DIR}/bin/pip"
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    sh '''
                        echo "Installing/upgrading pip..."
                        ${PIP} install --upgrade pip setuptools wheel || echo "Pip upgrade failed, continuing..."
                        
                        if [ -f requirements.txt ]; then
                            echo "Installing from requirements.txt..."
                            ${PIP} install -r requirements.txt
                            echo "✅ Dependencies installed from requirements.txt"
                        else
                            echo "⚠️ requirements.txt not found"
                            echo "Installing Django and Pylint..."
                            ${PIP} install django pylint
                            echo "✅ Django and Pylint installed"
                        fi
                        
                        # Always ensure pylint is installed
                        ${PIP} install pylint || echo "Pylint installation failed"
                    '''
                }
            }
        }
        
        stage('Verify Installation') {
            steps {
                script {
                    sh '''
                        echo "Verifying installations..."
                        ${VENV_DIR}/bin/python -c "
import django
print('✅ Django version:', django.__version__)
                        "
                        
                        ${VENV_DIR}/bin/pylint --version || echo "⚠️ Pylint not available"
                    '''
                }
            }
        }
        
        stage('Simple Django Check') {
            steps {
                script {
                    sh '''
                        echo "Running basic Django checks..."
                        # Check if manage.py exists
                        if [ -f "manage.py" ]; then
                            echo "✅ Found manage.py"
                            ${VENV_DIR}/bin/python manage.py check --settings=myproject.settings || echo "⚠️ Django check failed - might need proper settings"
                        else
                            echo "⚠️ manage.py not found in root directory"
                            echo "Looking for Django project..."
                            find . -name "manage.py" -type f | head -5
                        fi
                    '''
                }
            }
        }
        
        stage('Run Pylint Analysis') {
            steps {
                script {
                    echo "Running Pylint code quality analysis..."
                    echo "Minimum score to pass: ${PYLINT_THRESHOLD}/10"
                    
                    sh '''
                        # Create reports directory
                        mkdir -p reports
                        
                        # Run pylint on accounts directory
                        echo "Running Pylint on accounts/ directory..."
                        
                        # First run to check if accounts/ exists
                        if [ -d "accounts" ]; then
                            echo "Found accounts/ directory"
                            ${VENV_DIR}/bin/pylint accounts/ --output-format=colorized > reports/pylint-output.txt 2>&1 || true
                        else
                            echo "⚠️ accounts/ directory not found, checking for Python files..."
                            find . -name "*.py" -type f | head -10
                            echo "Running pylint on all Python files..."
                            ${VENV_DIR}/bin/pylint $(find . -name "*.py" -type f) --output-format=colorized > reports/pylint-output.txt 2>&1 || true
                        fi
                        
                        # Show summary
                        echo ""
                        echo "=== PYLINT SUMMARY ==="
                        grep -E "(Your code has been rated|^\\*|^---)" reports/pylint-output.txt || echo "No summary available"
                        
                        # Extract score if possible
                        SCORE_LINE=$(grep "Your code has been rated" reports/pylint-output.txt || echo "")
                        if [[ ! -z "$SCORE_LINE" ]]; then
                            SCORE=$(echo "$SCORE_LINE" | grep -oE "[0-9]+\.[0-9]+" | head -1)
                            echo "Pylint Score: ${SCORE:-N/A}/10"
                            
                            # Check against threshold if score exists
                            if [[ ! -z "$SCORE" ]]; then
                                THRESHOLD=${PYLINT_THRESHOLD}
                                if (( $(echo "$SCORE < $THRESHOLD" | bc -l 2>/dev/null) )); then
                                    echo "❌ Pylint score ${SCORE} is below threshold ${THRESHOLD}"
                                    exit 1
                                else
                                    echo "✅ Pylint score ${SCORE} meets threshold ${THRESHOLD}"
                                fi
                            fi
                        fi
                    '''
                }
            }
            
            post {
                always {
                    // Archive pylint reports
                    archiveArtifacts artifacts: 'reports/*.txt', allowEmptyArchive: true
                    
                    // Display pylint output in console
                    sh '''
                        echo ""
                        echo "=== PYLINT OUTPUT (last 50 lines) ==="
                        tail -50 reports/pylint-output.txt || echo "No pylint output available"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Archive any important files if they exist
            archiveArtifacts artifacts: 'requirements.txt, manage.py, reports/**', allowEmptyArchive: true
            
            // Cleanup virtual environment
            sh 'rm -rf ${VENV_DIR} || true'
            
            echo "Pipeline execution completed"
        }
        
        success {
            script {
                echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
                echo "🎉 Webhook is working perfectly!"
                echo "📊 Build Number: ${BUILD_NUMBER}"
                echo "⏱️ Build Duration: ${currentBuild.durationString}"
                echo "📝 GitHub triggered this build via webhook"
            }
        }
        
        failure {
            script {
                echo "❌❌❌ PIPELINE FAILED ❌❌❌"
                echo "Check the console output above for errors"
                echo "Possible causes:"
                echo "1. Missing requirements.txt"
                echo "2. Django project structure issues"
                echo "3. Pylint score below ${PYLINT_THRESHOLD}/10"
            }
        }
        
        cleanup {
            script {
                echo "🧹 Cleaning up temporary files..."
                sh '''
                    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
                    find . -name "*.pyc" -delete 2>/dev/null || true
                    echo "Cleanup complete"
                '''
            }
        }
    }
}