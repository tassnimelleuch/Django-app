pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        VENV_DIR = 'venv'
        PYLINT_THRESHOLD = '9.0'
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
                    env.PYTHON = sh(script: 'which python3 || which python', returnStdout: true).trim()
                    echo "Using Python: ${env.PYTHON}"
                    sh """
                        ${PYTHON} --version
                        ${PYTHON} -m pip --version || echo 'pip not available globally'
                    """
                }
            }
        }

        stage('Create Virtual Environment') {
            steps {
                script {
                    sh """
                        set -e
                        ${PYTHON} -m venv ${VENV_DIR}
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
                        ${PIP} install --upgrade pip setuptools wheel

                        if [ -f requirements.txt ]; then
                            echo 'Installing project requirements...'
                            ${PIP} install -r requirements.txt
                        else
                            echo 'requirements.txt not found, installing baseline dependencies'
                            ${PIP} install django pytest pytest-cov pytest-html pylint pylint-django
                        fi

                        # Ensure test and lint tooling are always available
                        ${PIP} install --upgrade pytest pytest-cov pytest-html pylint pylint-django coverage
                    """
                }
            }
        }

        stage('Code Quality & Tests') {
            parallel {
                stage('Static Analysis - PyLint') {
                    steps {
                        script {
                            sh """
                                set -e
                                mkdir -p reports

                                TARGET='accounts'
                                if [ ! -d "$TARGET" ]; then
                                    echo "accounts/ directory not found, using repository root"
                                    TARGET='.'
                                fi

                                echo 'Generating JSON PyLint report...'
                                ${PYLINT} "$TARGET" --load-plugins=pylint_django \
                                    --django-settings-module=myproject.settings \
                                    --output-format=json > pylint-report.json || true

                                echo 'Generating readable PyLint output...'
                                ${PYLINT} "$TARGET" --load-plugins=pylint_django \
                                    --django-settings-module=myproject.settings \
                                    --output-format=text > pylint-output.txt || true

                                python - <<'EOF'
import os
import pathlib
import re
import sys

output = pathlib.Path('pylint-output.txt')
if not output.exists():
    print('PyLint output missing; failing stage.')
    sys.exit(1)

text = output.read_text(encoding='utf-8', errors='ignore')
match = re.search(r"Your code has been rated at ([0-9.]+)/10", text)
if not match:
    print('Could not determine PyLint score; failing stage.')
    sys.exit(1)

score = float(match.group(1))
threshold = float(os.environ.get('PYLINT_THRESHOLD', '9.0'))
print(f'PyLint score: {score}/10 (threshold {threshold})')
if score < threshold:
    sys.exit(1)
EOF
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
                                set -e
                                TARGETS=''
                                if [ -d 'tests' ]; then
                                    TARGETS="$TARGETS tests"
                                fi
                                if [ -d 'accounts/tests' ]; then
                                    TARGETS="$TARGETS accounts/tests"
                                fi
                                if [ -f 'test_health.py' ]; then
                                    TARGETS="$TARGETS test_health.py"
                                fi
                                if [ -z "$TARGETS" ]; then
                                    TARGETS='accounts'
                                fi

                                echo "Running pytest on:$TARGETS"
                                ${PYTEST} $TARGETS \
                                    --cov=accounts \
                                    --cov-report=xml:coverage.xml \
                                    --cov-report=html:htmlcov \
                                    --junitxml=junit.xml \
                                    --html=pytest-report.html \
                                    -v
                            """
                        }
                    }
                }
            }
        }

        stage('Generate Reports') {
            steps {
                script {
                    sh """
                        set -e
                        echo 'Test Execution Summary' > test-summary.txt
                        echo '=====================' >> test-summary.txt
                        date >> test-summary.txt
                        echo '' >> test-summary.txt

                        if [ -f junit.xml ]; then
                            echo 'JUnit Report: junit.xml' >> test-summary.txt
                        fi
                        if [ -f coverage.xml ]; then
                            echo 'Coverage Report: coverage.xml' >> test-summary.txt
                        fi
                        if [ -f pytest-report.html ]; then
                            echo 'Pytest HTML Report: pytest-report.html' >> test-summary.txt
                        fi
                        if [ -f pylint-output.txt ]; then
                            echo '' >> test-summary.txt
                            echo 'Recent PyLint summary:' >> test-summary.txt
                            tail -n 5 pylint-output.txt >> test-summary.txt
                        fi
                    """
                }
            }
        }
    }

    post {
        always {
            script {
                if (fileExists('junit.xml')) {
                    junit 'junit.xml'
                } else {
                    echo 'JUnit report not found; skipping test result publication'
                }

                if (fileExists('htmlcov/index.html')) {
                    publishHTML(target: [
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Test Coverage Report',
                        keepAll: true
                    ])
                } else {
                    echo 'Coverage HTML report missing; skipping publish'
                }

                if (fileExists('pytest-report.html')) {
                    publishHTML(target: [
                        reportDir: '.',
                        reportFiles: 'pytest-report.html',
                        reportName: 'Pytest Detailed Report',
                        keepAll: true
                    ])
                } else {
                    echo 'Pytest HTML report missing; skipping publish'
                }
            }

            archiveArtifacts artifacts: 'junit.xml, coverage.xml, pylint-report.json, pylint-output.txt, test-summary.txt, pytest-report.html, htmlcov/**', allowEmptyArchive: true
            sh 'rm -rf ${VENV_DIR} || true'
        }

        success {
            script {
                echo 'Pipeline succeeded! ✅'
                echo "Coverage report: ${BUILD_URL}Coverage_20Report/"
                echo "Detailed pytest report: ${BUILD_URL}Pytest_20Detailed_20Report/"
            }
        }

        unstable {
            script {
                echo 'Pipeline completed with test failures! ⚠️'
                echo "Check the Test Results tab for build ${BUILD_NUMBER}"
            }
        }

        failure {
            script {
                echo 'Pipeline failed! ❌'
                echo 'Inspect the console output for root causes.'
            }
        }

        cleanup {
            script {
                echo 'Cleaning up workspace artifacts...'
                sh '''
                    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
                    find . -name "*.pyc" -delete 2>/dev/null || true
                '''
            }
        }
    }
}