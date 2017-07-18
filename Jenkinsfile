pipeline {
    agent any
    environment {
        mypy_args = "--junit-xml=reports/mypy.xml"
        pytest_args = "--junitxml=reports/junit-{env:OS:UNKNOWN_OS}-{envname}.xml --junit-prefix={env:OS:UNKNOWN_OS}  --basetemp={envtmpdir}"
    }
    parameters {
        string(name: "PROJECT_NAME", defaultValue: "HathiTrust Checksum Updater", description: "Name given to the project")
        booleanParam(name: "UNIT_TESTS", defaultValue: true, description: "Run Automated Unit Tests")
        booleanParam(name: "STATIC_ANALYSIS", defaultValue: true, description: "Run static analysis tests")
        booleanParam(name: "PACKAGE", defaultValue: true, description: "Create a Packages")
        booleanParam(name: "DEPLOY", defaultValue: false, description: "Deploy SCCM")
        booleanParam(name: "BUILD_DOCS", defaultValue: true, description: "Build documentation")
        booleanParam(name: "UPDATE_DOCS", defaultValue: false, description: "Update the documentation")
        string(name: 'URL_SUBFOLDER', defaultValue: "hathi_checksum_updater", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Cloning Source") {
            agent any

            steps {
                deleteDir()
                checkout scm
                stash includes: '**', name: "Source", useDefaultExcludes: false
                stash includes: 'deployment.yml', name: "Deployment"

            }

        }

        stage("Unit tests") {
            when {
                expression { params.UNIT_TESTS == true }
            }
            steps {
                parallel(
                        "Windows": {
                            node(label: 'Windows') {
                                deleteDir()
                                unstash "Source"
                                bat "${env.TOX}  -e pytest"
                                junit 'reports/junit-*.xml'

                            }
                        },
                        "Linux": {
                            node(label: "!Windows") {
                                deleteDir()
                                unstash "Source"
                                withEnv(["PATH=${env.PYTHON3}/..:${env.PATH}"]) {
                                    sh "${env.TOX}  -e pytest"
                                }
                                junit 'reports/junit-*.xml'
                            }
                        }
                )
            }
        }
        stage("Documentation") {
            agent any
            when {
                expression { params.BUILD_DOCS == true }
            }
            steps {
                deleteDir()
                unstash "Source"
                withEnv(['PYTHON=${env.PYTHON3}']) {
                    sh """${env.PYTHON3} -m venv .env
                          . .env/bin/activate
                          pip install --upgrade pip
                          pip install -r requirements.txt
                          cd docs && make html
                        """
                    stash includes: '**', name: "Documentation source", useDefaultExcludes: false
                }
            }
            post {
                success {
                    sh 'tar -czvf sphinx_html_docs.tar.gz -C docs/build/html .'
                    archiveArtifacts artifacts: 'sphinx_html_docs.tar.gz'
                }
            }
        }
        stage("Packaging") {
            when {
                expression { params.PACKAGE == true }
            }
            steps {
                parallel(
                        "Windows Wheel": {
                            node(label: "Windows") {
                                deleteDir()
                                unstash "Source"
                                bat """${env.PYTHON3} -m venv .env
                                        call .env/Scripts/activate.bat
                                        pip install --upgrade pip setuptools
                                        pip install -r requirements.txt
                                        python setup.py bdist_wheel --universal
                                    """
                                archiveArtifacts artifacts: "dist/**", fingerprint: true
                            }
                        },
                        "Windows CX_Freeze MSI": {
                            node(label: "Windows") {
                                deleteDir()
                                unstash "Source"
                                bat """${env.PYTHON3} -m venv .env
                                       call .env/Scripts/activate.bat
                                       pip install -r requirements.txt
                                       python cx_setup.py bdist_msi --add-to-path=true -k --bdist-dir build/msi
                                       call .env/Scripts/deactivate.bat
                                    """
                                bat "build\\msi\\udhtchecksum.exe --pytest"
                                dir("dist") {
                                    stash includes: "*.msi", name: "msi"
                                }

                            }
                            node(label: "Windows") {
                                deleteDir()
                                git url: 'https://github.com/UIUCLibrary/ValidateMSI.git'
                                unstash "msi"
                                bat "call validate.bat -i"
                                archiveArtifacts artifacts: "*.msi", fingerprint: true
                            }
                        },
                        "Source Release": {
                            deleteDir()
                            unstash "Source"
                            sh "${env.PYTHON3} setup.py sdist"
                            archiveArtifacts artifacts: "dist/**", fingerprint: true
                        }
                )
            }
        }
        stage("Deploy - Staging") {
            agent any
            when {
                expression { params.DEPLOY == true && params.PACKAGE == true }
            }
            steps {
                deleteDir()
                unstash "msi"
                sh "rsync -rv ./ \"${env.SCCM_STAGING_FOLDER}/${params.PROJECT_NAME}/\""
                input("Deploy to production?")
            }
        }

        stage("Deploy - SCCM upload") {
            agent any
            when {
                expression { params.DEPLOY == true && params.PACKAGE == true }
            }
            steps {
                deleteDir()
                unstash "msi"
                sh "rsync -rv ./ ${env.SCCM_UPLOAD_FOLDER}/"
            }
            post {
                success {
                    git url: 'https://github.com/UIUCLibrary/sccm_deploy_message_generator.git'
                    unstash "Deployment"
                    sh """${env.PYTHON3} -m venv .env
                          . .env/bin/activate
                          pip install --upgrade pip
                          pip install setuptools --upgrade
                          python setup.py install
                          deploymessage deployment.yml --save=deployment_request.txt
                      """
                    archiveArtifacts artifacts: "deployment_request.txt"
                    echo(readFile('deployment_request.txt'))
                }
            }
        }
        stage("Update online documentation") {
            agent any
            when {
                expression { params.UPDATE_DOCS == true && params.BUILD_DOCS == true }
            }

            steps {
                deleteDir()
                script {
                    echo "Updating online documentation"
                    unstash "Documentation source"
                    try {
                        sh("rsync -rv -e \"ssh -i ${env.DCC_DOCS_KEY}\" docs/build/html/ ${env.DCC_DOCS_SERVER}/${params.URL_SUBFOLDER}/ --delete")
                    } catch (error) {
                        echo "Error with uploading docs"
                        throw error
                    }
                }
            }
        }
    }
}
