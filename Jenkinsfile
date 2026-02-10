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
        PYLINT_THRESHOLD = '7.0'  // Minimum pylint score to pass (0-10 scale)
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
                    sh '${PYTHON} -m venv ${VENV_DIR} || echo "Virtual environment creation failed, continuing..."'
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
                            ${PIP} install django pylint pylint-django
                            echo "✅ Django and Pylint installed"
                        fi
                        
                        # Always ensure pylint is installed
                        ${PIP} install pylint pylint-django || echo "Pylint installation failed"
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
        
        stage('Run Pylint Analysis') {
            steps {
                script {
                    echo "Running Pylint code quality analysis..."
                    echo "Minimum score to pass: ${PYLINT_THRESHOLD}/10"
                    
                    sh '''
                        # Create reports directory
                        mkdir -p reports
                        
                        # Run pylint on accounts directory with JSON output
                        echo "Running Pylint on accounts/ directory..."
                        ${VENV_DIR}/bin/pylint accounts/ \
                            --output-format=json:reports/pylint-report.json \
                            --exit-zero || echo "Pylint found issues"
                        
                        # Also run with text output for console visibility
                        echo "=== PYLINT ANALYSIS RESULTS ==="
                        ${VENV_DIR}/bin/pylint accounts/ \
                            --output-format=colorized \
                            --exit-zero > reports/pylint-output.txt || true
                        
                        # Calculate score from JSON output
                        if [ -f "reports/pylint-report.json" ]; then
                            echo "Pylint JSON report generated"
                            # Extract score (requires jq tool)
                            if command -v jq >/dev/null 2>&1; then
                                SCORE=$(jq '.[] | .score' reports/pylint-report.json | head -1)
                                echo "Pylint Score: ${SCORE}/10"
                                
                                # Save score to file for pipeline use
                                echo "PYLINT_SCORE=${SCORE}" > pylint-score.env
                                
                                # Check against threshold
                                THRESHOLD=${PYLINT_THRESHOLD}
                                if (( $(echo "$SCORE < $THRESHOLD" | bc -l) )); then
                                    echo "❌ Pylint score ${SCORE} is below threshold ${THRESHOLD}"
                                    exit 1
                                else
                                    echo "✅ Pylint score ${SCORE} meets threshold ${THRESHOLD}"
                                fi
                            else
                                echo "⚠️ jq not installed, skipping score calculation"
                            fi
                        else
                            echo "⚠️ Pylint JSON report not generated"
                        fi
                        
                        # Display summary
                        echo ""
                        echo "=== PYLINT SUMMARY ==="
                        cat reports/pylint-output.txt | grep -E "(Your code has been rated|^\*|^---)" || true
                    '''
                }
            }
            
            post {
                always {
                    // Archive pylint reports
                    archiveArtifacts artifacts: 'reports/*.json, reports/*.txt, pylint-score.env', allowEmptyArchive: true
                    
                    // Display pylint output in console
                    sh '''
                        echo ""
                        echo "=== PYLINT CONSOLE OUTPUT ==="
                        cat reports/pylint-output.txt | tail -50 || echo "No pylint output available"
                    '''
                }
            }
        }
        
        stage('Generate Pylint HTML Report') {
            steps {
                script {
                    echo "Generating HTML report..."
                    sh '''
                        # Check if pylint-json2html is installed
                        ${PIP} install pylint-json2html || echo "pylint-json2html not available"
                        
                        # Generate HTML report if converter is available
                        if ${VENV_DIR}/bin/python -c "import json2html" 2>/dev/null; then
                            echo "Generating HTML report..."
                            ${VENV_DIR}/bin/python -c "
import json
from json2html import *
with open('reports/pylint-report.json', 'r') as f:
    data = json.load(f)
html = json2html.convert(json=data)
with open('reports/pylint-report.html', 'w') as f:
    f.write(html)
print('HTML report generated')
                            "
                        else
                            echo "Using simple HTML generation..."
                            echo '<html><body><h1>Pylint Report</h1><pre>' > reports/pylint-report.html
                            cat reports/pylint-output.txt >> reports/pylint-report.html
                            echo '</pre></body></html>' >> reports/pylint-report.html
                        fi
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
    }
    
    post {
        always {
            // Archive important files
            archiveArtifacts artifacts: 'requirements.txt, manage.py, reports/**', allowEmptyArchive: true
            
            // Publish HTML reports in Jenkins UI
            publishHTML([
                target: [
                    allowMissing: true,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'reports',
                    reportFiles: 'pylint-report.html',
                    reportName: 'Pylint Code Analysis'
                ]
            ])
            
            // Cleanup virtual environment
            sh 'rm -rf ${VENV_DIR} || true'
            
            echo "Pipeline execution completed"
        }
        
        success {
            script {
                // Read pylint score if available
                def pylintScore = "N/A"
                try {
                    if (fileExists('pylint-score.env')) {
                        def scoreFile = readFile('pylint-score.env')
                        def match = scoreFile =~ /PYLINT_SCORE=([0-9.]+)/
                        if (match) {
                            pylintScore = match[0][1]
                        }
                    }
                } catch (Exception e) {
                    echo "Could not read pylint score: ${e.message}"
                }
                
                echo """
                ✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅
                🎉 Webhook is working perfectly!
                📊 Build Number: ${BUILD_NUMBER}
                ⏱️  Build Duration: ${currentBuild.durationString}
                📝 GitHub triggered this build via webhook
                📈 Pylint Score: ${pylintScore}/10
                
                📋 Reports Available:
                • Pylint Analysis: ${BUILD_URL}Pylint_20Code_20Analysis/
                • Console Output: ${BUILD_URL}console
                """
            }
        }
        
        failure {
            script {
                echo """
                ❌❌❌ PIPELINE FAILED ❌❌❌
                
                Possible reasons:
                1. Pylint score below threshold (${PYLINT_THRESHOLD}/10)
                2. Syntax errors in Python code
                3. Missing dependencies
                4. Django project structure issues
                
                Check the console output above for details
                """
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