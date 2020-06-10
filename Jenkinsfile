@Library("ds-utils")
import org.ds.*
@Library(["devpi", "PythonHelpers"]) _

def CONFIGURATIONS = [
    "3.6": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist: [
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.6-windowsservercore",
            tox_env: "py36",
            devpi_wheel_regex: "cp36"

        ],
    "3.7": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist:[
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.7",
            tox_env: "py37",
            devpi_wheel_regex: "cp37"
        ],
    "3.8": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist:[
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.8",
            tox_env: "py38",
            devpi_wheel_regex: "cp38"
        ]
]



def get_package_version(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Version
        }
    }
}

def get_package_name(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Name
        }
    }
}

def remove_from_devpi(devpiExecutable, pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
    script {
                try {
                    bat "${devpiExecutable} login ${devpiUsername} --password ${devpiPassword}"
                    bat "${devpiExecutable} use ${devpiIndex}"
                    bat "${devpiExecutable} remove -y ${pkgName}==${pkgVersion}"
                } catch (Exception ex) {
                    echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
            }

    }
}

pipeline {
    agent none

    options {
        buildDiscarder logRotator(artifactDaysToKeepStr: '30', artifactNumToKeepStr: '30', daysToKeepStr: '100', numToKeepStr: '100')
    }
    triggers {
       parameterizedCron '@daily % DEPLOY_DEVPI=true; PACKAGE_CX_FREEZE=true'
    }
    parameters {
        string(name: "PROJECT_NAME", defaultValue: "HathiTrust Checksum Updater", description: "Name given to the project")
        booleanParam(name: "PACKAGE_CX_FREEZE", defaultValue: false, description: "Create a package with CX_Freeze")
        booleanParam(name: "DEPLOY_SCCM", defaultValue: false, description: "Create SCCM deployment package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Release Branch Only")
        booleanParam(name: "UPDATE_DOCS", defaultValue: false, description: "Update online documentation")
        string(name: 'URL_SUBFOLDER', defaultValue: "hathi_checksum_updater", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
           agent {
                dockerfile {
                    filename 'CI/docker/python/linux/Dockerfile'
                    label 'linux && docker'
                }
            }

            steps{
                sh "python setup.py dist_info"
            }
            post{
                success{
                    stash includes: "HathiChecksumUpdater.dist-info/**", name: 'DIST-INFO'
                    archiveArtifacts artifacts: "HathiChecksumUpdater.dist-info/**"
                }
            }
        }
        stage("Building") {

            stages{
                stage("Python Package"){
                    agent {
                        dockerfile {
                            filename 'CI/docker/python/linux/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps {
                        timeout(5){
                            sh(
                               label: "Building Python Package",
                               script:'''mkdir -p logs
                                         python setup.py build -b build'''
                            )
                        }
                    }
                }
                stage("Sphinx Documentation"){
                    agent {
                        dockerfile {
                            filename 'CI/docker/python/linux/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps{
                        timeout(5){
                            sh(
                               label: "Building docs",
                               script: '''mkdir -p logs
                               python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -w logs/build_sphinx.log -c docs/source
                                '''
                            )
                        }
                    }
                    post{
                        always {
                            archiveArtifacts artifacts: "logs/build_sphinx.log"
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            unstash "DIST-INFO"
                            script{
                                def props = readProperties interpolate: true, file: "HathiChecksumUpdater.dist-info/METADATA"
                                def DOC_ZIP_FILENAME = "${props.Name}-${props.Version}.doc.zip"
                                zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                            }
                        }
                    }
                }

            }
        }
        stage("Tests") {

            stages{
                stage("Run Tests"){
                    parallel {
                        stage("Run Pytest Unit Tests"){
                            environment{
                                junit_filename = "junit-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                            }
                            agent {
                                dockerfile {
                                    filename 'CI/docker/python/linux/Dockerfile'
                                    label 'linux && docker'
                                }
                            }
                            steps{
                                timeout(5){
                                    catchError(buildResult: "UNSTABLE", message: 'pytest found issues', stageResult: "UNSTABLE") {
                                        sh(
                                           label: "Running pytest",
                                           script: """mkdir -p reports/coverage
                                                      pytest --junitxml=reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:reports/coverage/ --cov=hathi_checksum
                                                      """
                                        )
                                    }
                                }
                            }
                            post {
                                always {
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                                    junit "reports/pytest/${env.junit_filename}"
                                }
                            }
                        }
                        stage("Run Flake8 Static Analysis") {
                            agent {
                                dockerfile {
                                    filename 'CI/docker/python/linux/Dockerfile'
                                    label 'linux && docker'
                                }
                            }
                            steps{
                                catchError(buildResult: "SUCCESS", message: 'flake8 found issues', stageResult: "UNSTABLE") {
                                    sh(
                                        label: "Running flake8",
                                        script: """mkdir -p logs
                                                   flake8 hathi_checksum --tee --output-file=logs/flake8.log
                                                   """
                                    )
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                }
                            }
                        }
                        stage("DocTest"){
                            agent {
                                dockerfile {
                                    filename 'CI/docker/python/linux/Dockerfile'
                                    label 'linux && docker'
                                }
                            }
                            steps{
                                timeout(5){
                                    catchError(buildResult: "SUCCESS", message: 'Doctest found issues', stageResult: "UNSTABLE") {
                                        sh(
                                            label: "Running Doctest",
                                            script: """mkdir -p logs
                                                       python -m sphinx -b doctest docs/source build/docs -d build/docs/.doctrees -w logs/doctest.log -c docs/source
                                                       """
                                        )
                                    }
                                }
                            }
                            post{
                                always {
                                    archiveArtifacts artifacts: 'logs/doctest.log'
                                    recordIssues(tools: [sphinxBuild(id: 'Doctest', name: 'DocTest', pattern: 'logs/doctest.log')])
                                }
                            }
                        }
                        stage("MyPy"){
                            agent {
                                dockerfile {
                                    filename 'CI/docker/python/linux/Dockerfile'
                                    label 'linux && docker'
                                }
                            }
                            steps{
                                timeout(5){
                                    catchError(buildResult: "SUCCESS", message: 'MyPy found issues', stageResult: "UNSTABLE") {
                                        sh (script: '''mkdir -p logs
                                                       mkdir -p reports/mypy_html
                                                       mypy -p hathi_checksum --html-report reports/mypy_html | tee logs/mypy.log
                                        '''
                                        )
                                    }
                                }
                            }
                            post{
                                always {
                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy_html', reportFiles: 'index.html', reportName: 'MyPy', reportTitles: ''])
                                }
                            }
                        }
                    }
                }
            }
        }
        stage("Packaging") {

            parallel {
                stage("Source and Wheel formats"){
                    agent {
                        dockerfile {
                            filename 'CI/docker/python/linux/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps{
                        timeout(5){
                            sh "python setup.py sdist --format zip -d dist bdist_wheel -d dist"
                        }
                        stash includes: 'dist/*.whl', name: "whl"
                        stash includes: 'dist/*.zip', name: "sdist"

                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                        }
                    }
                }
                stage("Windows CX_Freeze MSI"){
                    when{
                        equals expected: true, actual: params.PACKAGE_CX_FREEZE
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'CI/docker/python/windows/Dockerfile'
                            label "windows && docker"
                        }
                    }
                    steps{
                        timeout(10){
                            bat(
                                label: "Freezing to msi installer",
                                script:"python cx_setup.py bdist_msi --add-to-path=true -k --bdist-dir build/msi -d dist"
                                )
                        }


                    }
                    post{
                        success{
                            dir("dist") {
                                stash includes: "*.msi", name: "msi"
                            }
                            archiveArtifacts artifacts: "dist/*.msi", fingerprint: true
                        }
                    }
                }
            }
        }

//          stage("Deploy to DevPi") {
//             when {
//                 allOf{
//                     anyOf{
//                         equals expected: true, actual: params.DEPLOY_DEVPI
//                         triggeredBy "TimerTriggerCause"
//                     }
//                     anyOf {
//                         equals expected: "master", actual: env.BRANCH_NAME
//                         equals expected: "dev", actual: env.BRANCH_NAME
//                     }
//                 }
//             }
//             options{
//                 timestamps()
//             }
//
//             environment{
//                 PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${PATH}"
//                 PKG_NAME = get_package_name("DIST-INFO", "HathiChecksumUpdater.dist-info/METADATA")
//                 PKG_VERSION = get_package_version("DIST-INFO", "HathiChecksumUpdater.dist-info/METADATA")
//                 DEVPI = credentials("DS_devpi")
//             }
//             stages{
//                 stage("Install DevPi Client"){
//                     steps{
//                         bat "pip install devpi-client"
//                     }
//                 }
//                 stage("Upload to DevPi Staging"){
//                     steps {
//                         unstash "DOCS_ARCHIVE"
//                         unstash "whl"
//                         unstash "sdist"
//                         bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"
//
//                     }
//                 }
//                 stage("Test DevPi packages") {
//                     when {
//                         allOf{
//                             equals expected: true, actual: params.DEPLOY_DEVPI
//                             anyOf {
//                                 equals expected: "master", actual: env.BRANCH_NAME
//                                 equals expected: "dev", actual: env.BRANCH_NAME
//                             }
//                         }
//                     }
//                     parallel {
//                         stage("Testing Submitted Source Distribution") {
//                             environment {
//                                 PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
//                             }
//                             agent {
//                                 node {
//                                     label "Windows && Python3"
//                                 }
//                             }
//                             options {
//                                 skipDefaultCheckout(true)
//
//                             }
//                             stages{
//                                 stage("Creating venv to test sdist"){
//                                     steps {
//                                         lock("system_python_${NODE_NAME}"){
//                                             bat "python -m venv venv"
//                                         }
//                                         bat "venv\\Scripts\\python.exe -m pip install pip --upgrade && venv\\Scripts\\pip.exe install setuptools --upgrade && venv\\Scripts\\pip.exe install \"tox<3.7\" detox devpi-client"
//                                     }
//
//                                 }
//                                 stage("Testing DevPi zip Package"){
//                                     options{
//                                         timeout(20)
//                                     }
//                                     environment {
//                                         PATH = "${tool 'cmake3.12'};${WORKSPACE}\\venv\\Scripts;$PATH"
//                                         CL = "/MP"
//                                     }
//                                     steps {
//                                         devpiTest(
//                                             devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                                             url: "https://devpi.library.illinois.edu",
//                                             index: "${env.BRANCH_NAME}_staging",
//                                             pkgName: "${env.PKG_NAME}",
//                                             pkgVersion: "${env.PKG_VERSION}",
//                                             pkgRegex: "zip",
//                                             detox: false
//                                         )
//                                         echo "Finished testing Source Distribution: .zip"
//                                     }
//
//                                 }
//                             }
//                             post {
//                                 cleanup{
//                                     cleanWs(
//                                         deleteDirs: true,
//                                         disableDeferredWipeout: true,
//                                         patterns: [
//                                             [pattern: '*tmp', type: 'INCLUDE'],
//                                             [pattern: 'source', type: 'INCLUDE'],
//                                             [pattern: 'certs', type: 'INCLUDE']
//                                             ]
//                                     )
//                                 }
//                             }
//
//                         }
//                         stage("Built Distribution: .whl") {
//                             agent {
//                                 node {
//                                     label "Windows && Python3"
//                                 }
//                             }
//                             environment {
//                                 PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
//                             }
//                             options {
//                                 skipDefaultCheckout(true)
//                             }
//                             stages{
//                                 stage("Creating venv to Test Whl"){
//                                     steps {
//                                         lock("system_python_${NODE_NAME}"){
//                                             bat "if not exist venv\\36 mkdir venv\\36"
//                                             bat "\"${tool 'CPython-3.6'}\\python.exe\" -m venv venv\\36"
//                                             bat "if not exist venv\\37 mkdir venv\\37"
//                                             bat "\"${tool 'CPython-3.7'}\\python.exe\" -m venv venv\\37"
//                                         }
//                                         bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
//                                     }
//
//                                 }
//                                 stage("Testing DevPi .whl Package"){
//                                     options{
//                                         timeout(20)
//                                     }
//                                     environment {
//                                         PATH = "${WORKSPACE}\\venv\\36\\Scripts;${WORKSPACE}\\venv\\37\\Scripts;$PATH"
//                                     }
//                                     steps {
//                                         echo "Testing Whl package in devpi"
//                                         devpiTest(
//                                                 devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                                                 url: "https://devpi.library.illinois.edu",
//                                                 index: "${env.BRANCH_NAME}_staging",
//                                                 pkgName: "${env.PKG_NAME}",
//                                                 pkgVersion: "${env.PKG_VERSION}",
//                                                 pkgRegex: "whl",
//                                                 detox: false
//                                             )
//
//                                         echo "Finished testing Built Distribution: .whl"
//                                     }
//                                 }
//
//                             }
//                             post {
//                                 cleanup{
//                                     cleanWs(
//                                         deleteDirs: true,
//                                         disableDeferredWipeout: true,
//                                         patterns: [
//                                             [pattern: 'source', type: 'INCLUDE'],
//                                             [pattern: '*tmp', type: 'INCLUDE'],
//                                             [pattern: 'certs', type: 'INCLUDE']
//                                             ]
//                                     )
//                                 }
//                             }
//                         }
//                     }
//                 }
//                 stage("Deploy to DevPi Production") {
//                     when {
//                         allOf{
//                             equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
//                             branch "master"
//                         }
//                     }
//                     steps {
//                         script {
//                             try{
//                                 timeout(30) {
//                                     input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
//                                 }
//                                 bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
//
//                                 bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
//                                 bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
//                             } catch(err){
//                                 echo "User response timed out. Packages not deployed to DevPi Production."
//                             }
//                         }
//
//                     }
//                 }
//             }
//             post {
//                 success {
//                     echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
//                     script {
//                         bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
//                         bat "venv\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging"
//                         bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
//                     }
//                 }
//                 failure {
//                     echo "At least one package format on DevPi failed."
//                 }
//                 cleanup{
//                     remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
//                 }
//             }
//         }
        stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
                beforeAgent true
            }
            options{
                timestamps()
                lock("hathi_checksum-devpi")
            }
            environment{
                DEVPI = credentials("DS_devpi")
            }
            stages{
                stage("Deploy to Devpi Staging") {
                    agent {
                        dockerfile {
                            filename 'CI/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                        unstash 'DOCS_ARCHIVE'
                        unstash 'PYTHON_PACKAGES'
                        sh(
                                label: "Connecting to DevPi Server",
                                script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                            )
                        sh(
                            label: "Uploading to DevPi Staging",
                            script: """devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi
devpi upload --from-dir dist --clientdir ${WORKSPACE}/devpi"""
                        )
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: "dist/", type: 'INCLUDE'],
                                    [pattern: "devpi/", type: 'INCLUDE'],
                                    [pattern: 'build/', type: 'INCLUDE']
                                ]
                            )
                        }
                    }
                }
                stage("Test DevPi packages") {
                    matrix {
                        axes {
                            axis {
                                name 'FORMAT'
                                values 'zip', "whl"
                            }
                            axis {
                                name 'PYTHON_VERSION'
                                values '3.6', "3.7"
                            }
                        }
                        agent {
                          dockerfile {
                            additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image}"
                            filename 'CI/docker/deploy/devpi/test/windows/Dockerfile'
                            label 'windows && docker'
                          }
                        }
                        stages{
                            stage("Testing DevPi Package"){
                                options{
                                    timeout(10)
                                }
                                steps{
                                    script{
                                        unstash "DIST-INFO"
                                        def props = readProperties interpolate: true, file: 'HathiChecksumUpdater.dist-info/METADATA'
                                        bat(
                                            label: "Connecting to Devpi Server",
                                            script: "devpi use https://devpi.library.illinois.edu --clientdir certs\\ && devpi login %DEVPI_USR% --password %DEVPI_PSW% --clientdir certs\\ && devpi use ${env.BRANCH_NAME}_staging --clientdir certs\\"
                                        )
                                        bat(
                                            label: "Testing ${FORMAT} package stored on DevPi with Python version ${PYTHON_VERSION}",
                                            script: "devpi test --index ${env.BRANCH_NAME}_staging ${props.Name}==${props.Version} -s ${FORMAT} --clientdir certs\\ -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v"
                                        )
                                    }
                                }
                                post{
                                    cleanup{
                                        cleanWs(
                                            deleteDirs: true,
                                            patterns: [
                                                [pattern: "dist/", type: 'INCLUDE'],
                                                [pattern: "certs/", type: 'INCLUDE'],
                                                [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                                                [pattern: 'build/', type: 'INCLUDE']
                                            ]
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

            }
            post{
                success{
                    node('linux && docker') {
                       script{
                            docker.build("uiucpresconpackager:devpi.${env.BUILD_ID}",'-f ./CI/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'HathiChecksumUpdater.dist-info/METADATA'
                                sh(
                                    label: "Connecting to DevPi Server",
                                    script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                )
                                sh(
                                    label: "Selecting to DevPi index",
                                    script: "devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi"
                                )
                                sh(
                                    label: "Pushing package to DevPi index",
                                    script:  "devpi push ${props.Name}==${props.Version} DS_Jenkins/${env.BRANCH_NAME} --clientdir ${WORKSPACE}/devpi"
                                )
                            }
                       }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            docker.build("uiucpresconpackager:devpi.${env.BUILD_ID}",'-f ./CI/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'HathiChecksumUpdater.dist-info/METADATA'
                                sh(
                                    label: "Connecting to DevPi Server",
                                    script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                )
                                sh(
                                    label: "Selecting to DevPi index",
                                    script: "devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi"
                                )
                                sh(
                                    label: "Removing package to DevPi index",
                                    script: "devpi remove -y ${props.Name}==${props.Version} --clientdir ${WORKSPACE}/devpi"
                                )
                                cleanWs(
                                    deleteDirs: true,
                                    patterns: [
                                        [pattern: "dist/", type: 'INCLUDE'],
                                        [pattern: "devpi/", type: 'INCLUDE'],
                                        [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                                        [pattern: 'build/', type: 'INCLUDE']
                                    ]
                                )
                            }
                       }
                    }
                }
            }
        }
        stage("Deployment"){
            parallel{

                stage("Deploy - SCCM"){
                    agent any
                    when {
                        equals expected: true, actual: params.DEPLOY_SCCM
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Deploy - Staging") {



                            steps {
                                deployStash("msi", "${env.SCCM_STAGING_FOLDER}/${params.PROJECT_NAME}/")
                                input("Deploy to production?")
                            }
                        }

                        stage("Deploy - SCCM upload") {

                            steps {
                                deployStash("msi", "${env.SCCM_UPLOAD_FOLDER}")
                            }
                        }
                        stage("Creating Deployment request"){
                            steps{
                                script{
                                    unstash "Source"
                                    def  deployment_request = requestDeploy this, "deployment.yml"
                                    echo deployment_request
                                    writeFile file: "deployment_request.txt", text: deployment_request
                                    archiveArtifacts artifacts: "deployment_request.txt"
                                }
                            }
                        }
                    }
                }
                stage("Documentation Deployment"){
                    agent any
                    when {
                        equals expected: true, actual: params.UPDATE_DOCS
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Update online documentation") {
                            options{
                               timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                            }
                            steps {
                                dir("build/docs/html/"){
                                    bat "dir /s /B"
                                    sshPublisher(
                                        publishers: [
                                            sshPublisherDesc(
                                                configName: 'apache-ns - lib-dccuser-updater',
                                                sshLabel: [label: 'Linux'],
                                                transfers: [sshTransfer(excludes: '',
                                                execCommand: '',
                                                execTimeout: 120000,
                                                flatten: false,
                                                makeEmptyDirs: false,
                                                noDefaultExcludes: false,
                                                patternSeparator: '[, ]+',
                                                remoteDirectory: "${params.URL_SUBFOLDER}",
                                                remoteDirectorySDF: false,
                                                removePrefix: '',
                                                sourceFiles: '**')],
                                            usePromotionTimestamp: false,
                                            useWorkspaceInPromotion: false,
                                            verbose: true
                                            )
                                        ]
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
