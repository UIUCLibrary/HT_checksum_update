@Library("ds-utils")
import org.ds.*
@Library(["devpi", "PythonHelpers"]) _


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
    agent {
        label "Windows"
    }

    environment {
        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
        PKG_NAME = pythonPackageName(toolName: "CPython-3.6")
        PKG_VERSION = pythonPackageVersion(toolName: "CPython-3.6")
        DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
        DEVPI = credentials("DS_devpi")
        mypy_args = "--junit-xml=mypy.xml"
        pytest_args = "--junitxml=reports/junit-{env:OS:UNKNOWN_OS}-{envname}.xml --junit-prefix={env:OS:UNKNOWN_OS}  --basetemp={envtmpdir}"
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
//        timeout(60)  // Timeout after 60 minutes. This shouldn't take this long but it hangs for some reason
        checkoutToSubdirectory("source")
    }
    triggers {
        cron('@daily')
    }
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
        string(name: "PROJECT_NAME", defaultValue: "HathiTrust Checksum Updater", description: "Name given to the project")
        booleanParam(name: "TEST_RUN_PYTEST", defaultValue: true, description: "Run PyTest unit tests")
        booleanParam(name: "TEST_RUN_DOCTEST", defaultValue: true, description: "Test documentation")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy static analysis")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 Tests")
        booleanParam(name: "PACKAGE_CX_FREEZE", defaultValue: true, description: "Create a package with CX_Freeze")
        booleanParam(name: "DEPLOY_SCCM", defaultValue: false, description: "Create SCCM deployment package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Release Branch Only")
        booleanParam(name: "UPDATE_DOCS", defaultValue: false, description: "Update online documentation")
        string(name: 'URL_SUBFOLDER', defaultValue: "hathi_checksum_updater", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Configure") {
            options{
                timeout(10)  // Timeout after 10 minutes. This shouldn't take this long but it hangs for some reason
            }
            stages{
                stage("Purge all existing data in workspace"){
                    when{
                        anyOf{
                            equals expected: true, actual: params.FRESH_WORKSPACE
                            triggeredBy "TimerTriggerCause"
                        }
                    }
                    steps {
                        deleteDir()
                        dir("source"){
                            checkout scm
                        }
                    }
                }
                stage("Stashing important files for later"){
                    steps{
                        dir("source"){
                            stash includes: 'deployment.yml', name: "Deployment"
                        }
                    }
                }
                stage("Creating virtualenv for building"){
                    steps{
                        bat "python -m venv venv"
                        script {
                            try {
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip>=18.1"
                            }
                            catch (exc) {
                                bat "python -m venv venv"
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip>=18.0 --no-cache-dir"
                            }                           
                        }    
                        bat "venv\\Scripts\\pip.exe install sphinx wheel \"pluggy>=0.7\" -r source\\requirements.txt --upgrade-strategy only-if-needed"

                    }
                    post{
                        success{
                            bat "(if not exist logs mkdir logs) && venv\\Scripts\\pip.exe list > ${WORKSPACE}\\logs\\pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_venv_${NODE_NAME}.log"
                        }
                        failure {
                            deleteDir()
                        }
                        cleanup{
                            cleanWs(patterns: [[pattern: 'logs/pippackages_venv_*.log', type: 'INCLUDE']])
                        }
                    }
                }
            }
            post{
                success{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }
                failure {
                    deleteDir()
                }

            }
        }
        stage("Building") {
            environment {
                PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
            }
            stages{
                stage("Python Package"){
                    options{
                       timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                    }
                    steps {
                        dir("source"){
                            powershell "& python setup.py build -b ${WORKSPACE}\\build  | tee ${WORKSPACE}\\logs\\build.log"
                        }

                    }
                    post{
                        always{
                            recordIssues(tools: [
                                    pyLint(name: 'Setuptools Build: PyLint', pattern: 'logs/build.log'),
                                ]
                            )
                            archiveArtifacts artifacts: "logs/build.log"
                        }
                        failure{
                            echo "Failed to build Python package"
                        }
                    }
                }
                stage("Sphinx Documentation"){
                    options{
                       timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                    }
                    steps{
                        echo "Building docs on ${env.NODE_NAME}"
                        bat "pip install sphinx && sphinx-build source/docs/source build/docs/html -d build/docs/.doctrees -w logs\\build_sphinx.log -c source/docs/source"
                    }
                    post{
                        always {
                            archiveArtifacts artifacts: "logs/build_sphinx.log"
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${env.DOC_ZIP_FILENAME}"
                            stash includes: "dist/${env.DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                        }
                        failure{
                            echo "Failed to build Python package"
                        }
                    }
                }

            }
        }
        stage("Tests") {
            environment {
                PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
            }
            stages{
                stage("Install Python Testing Tools"){
                    steps{
                        bat "pip install tox mypy lxml pytest pytest-cov flake8"
                    }
                }
                stage("Run Tests"){
                    parallel {
                        stage("Run Pytest Unit Tests"){
                            when {
                               equals expected: true, actual: params.TEST_RUN_PYTEST
                            }
                            options{
                               timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                            }
                            environment{
                                junit_filename = "junit-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                            }
                            steps{
                                bat "if not exist reports\\coverage mkdir reports\\coverage"
                                 dir("source"){
                                    bat "pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/ --cov=hathi_checksum"
                                }
                            }
                            post {
                                always {
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                                    junit "reports/pytest/${env.junit_filename}"
                                }
                            }
                        }
//                        stage("PyTest"){
//                            options{
//                               timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
//                            }
//                            when {
//                                equals expected: true, actual: params.TEST_RUN_PYTEST
//                            }
//                            steps{
//                                dir("source"){
//                                    bat "pytest.exe --junitxml=${WORKSPACE}/reports/junit-${env.NODE_NAME}-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/coverage/ --cov=hathi_checksum" //  --basetemp={envtmpdir}"
//                                }
//
//                            }
//                            post {
//                                always{
//                                    dir("reports"){
//                                        script{
//                                            def report_files = findFiles glob: '**/*.pytest.xml'
//                                            report_files.each { report_file ->
//                                                echo "Found ${report_file}"
//                                                // archiveArtifacts artifacts: "${log_file}"
//                                                junit "${report_file}"
//                                                bat "del ${report_file}"
//                                            }
//                                        }
//                                    }
//                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
//                                }
//                            }
//                        }
                        stage("Run Flake8 Static Analysis") {
                            when {
                                equals expected: true, actual: params.TEST_RUN_FLAKE8
                            }
                            steps{
                                script{

                                    try{
                                        dir("source"){
                                            bat "flake8 hathi_checksum --tee --output-file=${WORKSPACE}\\logs\\flake8.log"
                                        }
                                    } catch (exc) {
                                        echo "flake8 found some warnings"
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                }
                            }
                        }
                        stage("DocTest"){
                            when{
                                equals expected: true, actual: params.TEST_RUN_DOCTEST
                            }
                            options{
                               timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                            }
                            steps{
                                bat "sphinx-build -b doctest docs\\source build\\docs -d build/docs/.doctrees -w logs\\doctest.log -c source/docs/source"
                            }
                            post{
                                always {
                                    archiveArtifacts artifacts: 'logs\\doctest.log'
                                    recordIssues(tools: [sphinxBuild(id: 'Doctest', name: 'DocTest', pattern: 'logs/doctest.log')])
                                }
                            }
                        }
                        stage("MyPy"){
                            when{
                                equals expected: true, actual: params.TEST_RUN_MYPY
                            }
                            options{
                               timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                            }
                            steps{
                                bat "if not exist logs mkdir logs"
                                dir("source") {
                                    bat "mypy -p hathi_checksum --junit-xml=${WORKSPACE}/logs/junit-${env.NODE_NAME}-mypy.xml --html-report ${WORKSPACE}/reports/mypy_html"
                                }
                            }
                            post{
                                always {
                                    junit "logs/junit-${env.NODE_NAME}-mypy.xml"
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
                    options{
                       timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                    }
                    steps{
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\scripts\\python.exe setup.py sdist --format zip -d ${WORKSPACE}\\dist bdist_wheel -d ${WORKSPACE}\\dist"
                        }
                        stash includes: 'dist/*.whl', name: "whl 3.6"
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
                    }
                    options {
                        timeout(10)  // Timeout after 10 minutes. This shouldn't take this long but it hangs for some reason
                    }
                    steps{
                        bat "if not exist dist mkdir dist"
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\python.exe cx_setup.py bdist_msi --add-to-path=true -k --bdist-dir ${WORKSPACE}/build/msi -d ${WORKSPACE}/dist"
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

         stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                        triggeredBy "TimerTriggerCause"
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            options{
                timestamps()
            }

            environment{
                PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${PATH}"

            }
            stages{
                stage("Install DevPi Client"){
                    steps{
                        bat "pip install devpi-client"
                    }
                }
                stage("Upload to DevPi Staging"){
                    steps {
                        unstash "DOCS_ARCHIVE"
                        unstash "whl 3.6"
                        unstash "sdist"
                        bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"

                    }
                }
                stage("Test DevPi packages") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI
                            anyOf {
                                equals expected: "master", actual: env.BRANCH_NAME
                                equals expected: "dev", actual: env.BRANCH_NAME
                            }
                        }
                    }
                    parallel {
                        stage("Testing Submitted Source Distribution") {
                            environment {
                                PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
                            }
                            agent {
                                node {
                                    label "Windows && Python3 && !Docker"
                                }
                            }
                            options {
                                skipDefaultCheckout(true)

                            }
                            stages{
                                stage("Creating venv to test sdist"){
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
                                            bat "python -m venv venv"
                                        }
                                        bat "venv\\Scripts\\python.exe -m pip install pip --upgrade && venv\\Scripts\\pip.exe install setuptools --upgrade && venv\\Scripts\\pip.exe install \"tox<3.7\" detox devpi-client"
                                    }

                                }
                                stage("Testing DevPi zip Package"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${tool 'cmake3.12'};${WORKSPACE}\\venv\\Scripts;$PATH"
                                        CL = "/MP"
                                    }
                                    steps {
                                        devpiTest(
                                            devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "zip",
                                            detox: false
                                        )
                                        echo "Finished testing Source Distribution: .zip"
                                    }

                                }
                            }
                            post {
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                            }

                        }
                        stage("Built Distribution: .whl") {
                            agent {
                                node {
                                    label "Windows && Python3 && !Docker"
                                }
                            }
                            environment {
                                PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
                            }
                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test Whl"){
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
                                            bat "if not exist venv\\36 mkdir venv\\36"
                                            bat "\"${tool 'CPython-3.6'}\\python.exe\" -m venv venv\\36"
                                            bat "if not exist venv\\37 mkdir venv\\37"
                                            bat "\"${tool 'CPython-3.7'}\\python.exe\" -m venv venv\\37"
                                        }
                                        bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;${WORKSPACE}\\venv\\37\\Scripts;$PATH"
                                    }
                                    steps {
                                        echo "Testing Whl package in devpi"
                                        devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "whl",
                                                detox: false
                                            )

                                        echo "Finished testing Built Distribution: .whl"
                                    }
                                }

                            }
                            post {
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                            }
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            branch "master"
                        }
                    }
                    steps {
                        script {
                            try{
                                timeout(30) {
                                    input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
                                }
                                bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"

                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                                bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
                            } catch(err){
                                echo "User response timed out. Packages not deployed to DevPi Production."
                            }
                        }

                    }
                }
            }
            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
                        bat "venv\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging"
                        bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
                    }
                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
                cleanup{
                    remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
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
                stage("Update online documentation") {
                    agent any
                    when {
                        expression { params.UPDATE_DOCS == true }
                    }
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
    post{
        cleanup{
            script {
                cleanWs(
                    deleteDirs: true,
                    disableDeferredWipeout: true,
                    patterns: [
                        [pattern: 'dist', type: 'INCLUDE'],
    //                    [pattern: 'build', type: 'INCLUDE'],
                        [pattern: 'reports', type: 'INCLUDE'],
                        [pattern: 'logs', type: 'INCLUDE'],
                        [pattern: 'certs', type: 'INCLUDE'],
                        [pattern: '*tmp', type: 'INCLUDE'],
                        ]
                    )
            }
        }
        failure{
            echo "Pipeline failed. If the problem is old cached data, you might need to purge the testing environment. Try manually running the pipeline again with the parameter FRESH_WORKSPACE checked."
        }
    }
}
