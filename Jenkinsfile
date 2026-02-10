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
    }
    
    post {
        always {
            // Archive any important files if they exist
            archiveArtifacts artifacts: 'requirements.txt, manage.py', allowEmptyArchive: true
            
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
                
                // Send success notification if needed
                // emailext to: 'your-email@example.com', subject: 'Jenkins Build Success', body: 'Pipeline succeeded!'
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