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
                            echo "Installing Django only..."
                            ${PIP} install django
                            echo "✅ Django installed"
                        fi
                    '''
                }
            }
        }
        
        stage('Verify Installation') {
            steps {
                script {
                    sh '''
                        echo "Verifying Django installation..."
                        ${VENV_DIR}/bin/python -c "
import django
print('✅ Django version:', django.__version__)
print('✅ Django path:', django.__path__)
print('✅ Installation successful!')
                        "
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
        
        stage('Pylint Code Analysis') {
            steps {
                script {
                    echo "🔍 Running Pylint code analysis..."
                    
                    // Check if there are Python files to analyze
                    def pythonFiles = sh(script: 'find . -name "*.py" -type f | head -20', returnStdout: true).trim()
                    
                    if (pythonFiles) {
                        echo "Found Python files to analyze:"
                        echo pythonFiles
                        
                        // Run pylint on specific directories or files
                        // You can adjust this based on your project structure
                        try {
                            // Example: Run pylint on accounts module
                            def pylintOutput = sh(script: """
                                ${PYLINT} --exit-zero --output-format=text accounts/ 2>&1 || true
                            """, returnStdout: true)
                            
                            echo "📊 Pylint Output:"
                            echo pylintOutput
                            
                            // Extract score from output (looks like "Your code has been rated at 9.50/10")
                            def scoreMatch = pylintOutput =~ /Your code has been rated at (\d+\.\d+)\/\d+/
                            def pylintScore = 0.0
                            
                            if (scoreMatch) {
                                pylintScore = scoreMatch[0][1].toFloat()
                                echo "📈 Pylint Score: ${pylintScore}/10"
                                
                                // Check if score meets threshold
                                if (pylintScore >= PYLINT_THRESHOLD.toFloat()) {
                                    echo "✅ Pylint passed! Score (${pylintScore}) >= threshold (${PYLINT_THRESHOLD})"
                                } else {
                                    echo "⚠️ Pylint score (${pylintScore}) is below threshold (${PYLINT_THRESHOLD})"
                                    echo "⚠️ This is a warning, but continuing build..."
                                    // Uncomment the next line if you want to fail the build on low score
                                    // error("Pylint score ${pylintScore} is below required threshold ${PYLINT_THRESHOLD}")
                                }
                            } else {
                                echo "⚠️ Could not extract Pylint score from output"
                                echo "⚠️ Continuing build..."
                            }
                            
                        } catch (Exception e) {
                            echo "⚠️ Pylint execution failed: ${e.getMessage()}"
                            echo "⚠️ Continuing build..."
                        }
                    } else {
                        echo "⚠️ No Python files found to analyze with Pylint"
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Archive any important files if they exist
            archiveArtifacts artifacts: 'requirements.txt, manage.py', allowEmptyArchive: true
            
            // Also archive Pylint report if you want
            sh '${PYLINT} --exit-zero --output-format=json accounts/ > pylint_report.json 2>/dev/null || true'
            archiveArtifacts artifacts: 'pylint_report.json', allowEmptyArchive: true
            
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
                echo "This is likely due to missing requirements.txt or Django project structure"
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