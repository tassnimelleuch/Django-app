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
        
        stage('Pylint Code Analysis') {
            steps {
                script {
                    echo "🔍 Running Pylint code analysis..."
                    
                    try {
                        def pylintOutput = sh(script: """
                            ${PYLINT} --exit-zero accounts/ 2>&1
                        """, returnStdout: true)
                        
                        echo "Pylint Output:"
                        echo pylintOutput
                        
                        def scoreMatch = pylintOutput =~ /Your code has been rated at (\d+\.\d+)\/\d+/
                        def pylintScore = 0.0
                        
                        if (scoreMatch) {
                            pylintScore = scoreMatch[0][1].toFloat()
                            echo "Pylint Score: ${pylintScore}/10"
                            
                            if (pylintScore >= PYLINT_THRESHOLD.toFloat()) {
                                echo "✅ Pylint passed!"
                            } else {
                                echo "⚠️ Pylint score (${pylintScore}) is below threshold (${PYLINT_THRESHOLD})"
                                echo "Continuing build..."
                            }
                        }
                        
                    } catch (Exception e) {
                        echo "⚠️ Pylint execution failed: ${e.getMessage()}"
                        echo "Continuing build..."
                    }
                }
            }
        }
        
        stage('Run Pytest with Coverage') {
            steps {
                script {
                    echo "🧪 Running Pytest with coverage..."
                    
                    try {
                        sh """
                            ${PYTEST} accounts --cov
                        """
                        
                        echo "✅ Tests executed successfully"
                        
                    } catch (Exception e) {
                        echo "❌ Pytest execution failed: ${e.getMessage()}"
                        echo "Check if tests exist in the accounts module"
                        echo "Failing the build due to test failure"
                        error("Pytest tests failed")
                    }
                }
            }
        }
    }
    
    post {
        always {
            sh 'rm -rf ${VENV_DIR} || true'
            
            echo "Pipeline execution completed"
        }
        
        success {
            echo "✅✅✅ PIPELINE SUCCESSFUL! ✅✅✅"
            echo "📊 Build Number: ${BUILD_NUMBER}"
        }
        
        failure {
            echo "❌❌❌ PIPELINE FAILED ❌❌❌"
            echo "Check the console output above for errors"
        }
        
        cleanup {
            echo "🧹 Cleaning up..."
        }
    }
}