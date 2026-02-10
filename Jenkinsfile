pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        VENV_DIR = 'venv'
        PYLINT_THRESHOLD = '9.0'
        PYTHON = ''
        PIP = ''
        PYTEST = ''
        PYLINT = ''
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
                checkout scm
                echo 'Workspace prepared and source checked out'
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('Setup Python') {
            steps {
                script {
                    env.PYTHON = sh(script: 'which python3', returnStdout: true).trim()
                    if (!env.PYTHON) {
                        env.PYTHON = sh(script: 'which python', returnStdout: true).trim()
                    }
                    echo "Using Python: ${env.PYTHON}"
                    sh """
                        ${env.PYTHON} --version
                        ${env.PYTHON} -m pip --version || echo 'pip not available globally'
                    """
                }
            }
        }

        stage('Create Virtual Environment') {
            steps {
                script {
                    sh """
                        set -e
                        ${env.PYTHON} -m venv ${env.VENV_DIR}
                    """
                    env.PIP = "${env.VENV_DIR}/bin/pip"
                    env.PYTEST = "${env.VENV_DIR}/bin/pytest"
                    env.PYLINT = "${env.VENV_DIR}/bin/pylint"
                    echo "Virtual environment ready at ${env.VENV_DIR}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    sh """
                        set -e
                        ${env.PIP} install --upgrade pip setuptools wheel

                        if [ -f requirements.txt ]; then
                            echo 'Installing project requirements...'
                            ${env.PIP} install -r requirements.txt
                        else
                            echo 'requirements.txt not found, installing baseline dependencies'
                            ${env.PIP} install django pytest pytest-cov pytest-html pylint pylint-django
                        fi

                        # Ensure test and lint tooling are always available
                        ${env.PIP} install --upgrade pytest pytest-cov pytest-html pylint pylint-django coverage
                    """
                }
            }
        }

        stage('Code Quality & Tests') {
            parallel {
                stage('Static Analysis - PyLint') {
                    steps {
                        script {
                            // Determine target directory
                            def targetDir = 'accounts'
                            sh """
                                if [ ! -d "${targetDir}" ]; then
                                    echo "accounts/ directory not found, using repository root"
                                    targetDir='.'
                                fi
                                echo "PyLint target directory: \${targetDir}"
                            """
                            
                            sh """
                                set +e
                                mkdir -p reports

                                echo 'Generating JSON PyLint report...'
                                ${env.PYLINT} "\${targetDir}" --load-plugins=pylint_django \
                                    --django-settings-module=myproject.settings \
                                    --output-format=json > pylint-report.json 2>&1

                                echo 'Generating readable PyLint output...'
                                ${env.PYLINT} "\${targetDir}" --load-plugins=pylint_django \
                                    --django-settings-module=myproject.settings \
                                    --output-format=text > pylint-output.txt 2>&1
                                
                                # Check PyLint score
                                PY_SCORE=\$(grep -o "Your code has been rated at [0-9.]\\+/10" pylint-output.txt | grep -o "[0-9.]\\+")
                                if [ -z "\$PY_SCORE" ]; then
                                    echo "ERROR: Could not extract PyLint score"
                                    echo "PyLint output:"
                                    cat pylint-output.txt
                                    exit 1
                                fi
                                
                                echo "PyLint score: \$PY_SCORE/10"
                                THRESHOLD=${env.PYLINT_THRESHOLD}
                                
                                # Compare scores
                                if python3 -c "import sys; sys.exit(0 if float('$PY_SCORE') >= float('$THRESHOLD') else 1)"; then
                                    echo "PyLint score meets threshold of \$THRESHOLD"
                                    exit 0
                                else
                                    echo "ERROR: PyLint score (\$PY_SCORE) below threshold (\$THRESHOLD)"
                                    exit 1
                                fi
                            """
                        }
                    }

                    post {
                        always {
                            archiveArtifacts artifacts: 'pylint-output.txt, pylint-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Unit Tests - Pytest') {
                    steps {
                        script {
                            sh """
                                set +e
                                TARGETS=''
                                
                                # Check for various test locations
                                if [ -d 'tests' ]; then
                                    TARGETS="\${TARGETS} tests"
                                fi
                                
                                if [ -d 'accounts/tests' ]; then
                                    TARGETS="\${TARGETS} accounts/tests"
                                fi
                                
                                if [ -f 'test_health.py' ]; then
                                    TARGETS="\${TARGETS} test_health.py"
                                fi
                                
                                if [ -z "\${TARGETS}" ]; then
                                    TARGETS='.'
                                fi
                                
                                echo "Running pytest on: \${TARGETS}"
                                
                                ${env.PYTEST} \${TARGETS} \
                                    --cov=. \
                                    --cov-report=xml:coverage.xml \
                                    --cov-report=html:htmlcov \
                                    --junitxml=junit.xml \
                                    --html=pytest-report.html \
                                    -v
                                
                                # Capture pytest exit code but don't fail yet
                                PYTEST_EXIT=\$?
                                
                                # Generate JUnit and coverage reports even if tests fail
                                echo "Pytest completed with exit code: \$PYTEST_EXIT"
                                
                                # Create a simple test summary
                                echo "Test Execution Summary" > test-summary.txt
                                echo "=====================" >> test-summary.txt
                                date >> test-summary.txt
                                echo "" >> test-summary.txt
                                
                                if [ -f junit.xml ]; then
                                    echo "Test results saved to junit.xml" >> test-summary.txt
                                fi
                                
                                if [ -f coverage.xml ]; then
                                    echo "Coverage report saved to coverage.xml" >> test-summary.txt
                                fi
                                
                                # Exit with pytest's exit code
                                exit \$PYTEST_EXIT
                            """
                        }
                    }
                    
                    post {
                        always {
                            archiveArtifacts artifacts: 'junit.xml, coverage.xml, pytest-report.html, htmlcov/**, test-summary.txt', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Generate Reports') {
            steps {
                script {
                    sh """
                        echo 'Finalizing reports...'
                        if [ -f pylint-output.txt ]; then
                            echo '' >> test-summary.txt
                            echo 'PyLint Summary:' >> test-summary.txt
                            tail -n 10 pylint-output.txt >> test-summary.txt
                        fi
                        
                        if [ -f coverage.xml ]; then
                            echo '' >> test-summary.txt
                            echo 'Coverage Summary:' >> test-summary.txt
                            grep -o 'line-rate="[0-9.]*"' coverage.xml | head -1 >> test-summary.txt
                        fi
                    """
                }
            }
        }
    }

    post {
        always {
            script {
                // Archive all reports
                archiveArtifacts artifacts: 'junit.xml, coverage.xml, pylint-report.json, pylint-output.txt, test-summary.txt, pytest-report.html, htmlcov/**', allowEmptyArchive: true
                
                // Publish HTML reports if they exist
                if (fileExists('htmlcov/index.html')) {
                    publishHTML(target: [
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report',
                        keepAll: true
                    ])
                } else {
                    echo 'Coverage HTML report missing; skipping publish'
                }
                
                if (fileExists('pytest-report.html')) {
                    publishHTML(target: [
                        reportDir: '.',
                        reportFiles: 'pytest-report.html',
                        reportName: 'Pytest Report',
                        keepAll: true
                    ])
                } else {
                    echo 'Pytest HTML report missing; skipping publish'
                }
                
                // Cleanup
                sh 'rm -rf ${env.VENV_DIR} || true'
                sh '''
                    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
                    find . -name "*.pyc" -delete 2>/dev/null || true
                '''
            }
        }
        
        success {
            script {
                echo 'Pipeline succeeded! ✅'
                echo "Coverage report: ${BUILD_URL}Coverage_20Report/"
                echo "Detailed pytest report: ${BUILD_URL}Pytest_20Report/"
            }
        }
        
        failure {
            script {
                echo 'Pipeline failed! ❌'
                echo 'Inspect the console output for root causes.'
                echo "Build URL: ${BUILD_URL}"
            }
        }
        
        unstable {
            script {
                echo 'Pipeline completed with test failures! ⚠️'
                echo "Check the Test Results tab for build ${BUILD_NUMBER}"
            }
        }
    }
}